"""
Stage 6: Comparative Training & Evaluation Pipeline for Sketch Intelligence
Trains and compares Architecture A (Lightweight CNN) and Architecture B (ResNet18-Adapted).
Implements PyTorch AMP mixed precision, AdamW, Cosine Annealing, Early Stopping,
Top-5 accuracy, Macro Precision/Recall/F1, Confusion Matrix, and TU-Berlin external evaluation.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
import matplotlib.pyplot as plt

# Ensure backend is on PYTHONPATH
BASE_DIR = Path(r"C:\Sketch2Shape-AI")
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.sketch_intelligence.models import LightweightCNN, ResNet18Sketch

DATASET_DIR = BASE_DIR / "datasets" / "sketch_intelligence"
MODELS_DIR = BASE_DIR / "models" / "sketch_intelligence"
EXPERIMENTS_DIR = BASE_DIR / "experiments" / "sketch_intelligence"


def setup_device() -> torch.device:
    if torch.cuda.is_available():
        device = torch.device("cuda")
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"[DEVICE] Hardware Acceleration: {gpu_name} ({vram_gb:.2f} GB VRAM)")
    else:
        device = torch.device("cpu")
        print("[DEVICE] Running on CPU fallback.")
    return device


def load_datasets() -> Tuple[DataLoader, DataLoader, DataLoader, DataLoader, Dict[str, Any]]:
    print("\n[DATASET] Loading memory-mapped NumPy partitions from disk...")
    X_train = np.load(DATASET_DIR / "X_train.npy", mmap_mode="r")
    y_train = np.load(DATASET_DIR / "y_train.npy")
    X_val = np.load(DATASET_DIR / "X_val.npy", mmap_mode="r")
    y_val = np.load(DATASET_DIR / "y_val.npy")
    X_test = np.load(DATASET_DIR / "X_test.npy", mmap_mode="r")
    y_test = np.load(DATASET_DIR / "y_test.npy")

    tu_X = np.load(DATASET_DIR / "tu_berlin_X_test.npy", mmap_mode="r")
    tu_y = np.load(DATASET_DIR / "tu_berlin_y_test.npy")

    with open(MODELS_DIR / "class_mapping.json", "r", encoding="utf-8") as f:
        class_meta = json.load(f)

    # Convert to float tensors normalized to [0.0, 1.0] with channel dimension (B, 1, 128, 128)
    def make_loader(x_arr, y_arr, batch_size=128, shuffle=False):
        # Read in as contiguous float32 tensor
        x_tensor = torch.from_numpy(np.array(x_arr, dtype=np.float32)).unsqueeze(1) / 255.0
        y_tensor = torch.from_numpy(np.array(y_arr, dtype=np.int64))
        ds = TensorDataset(x_tensor, y_tensor)
        return DataLoader(ds, batch_size=batch_size, shuffle=shuffle, num_workers=0, pin_memory=True)

    batch_size = 128
    train_loader = make_loader(X_train, y_train, batch_size=batch_size, shuffle=True)
    val_loader = make_loader(X_val, y_val, batch_size=batch_size, shuffle=False)
    test_loader = make_loader(X_test, y_test, batch_size=batch_size, shuffle=False)
    tu_loader = make_loader(tu_X, tu_y, batch_size=batch_size, shuffle=False)

    print(f"  Train Loader : {len(y_train)} samples ({len(train_loader)} batches)")
    print(f"  Val Loader   : {len(y_val)} samples ({len(val_loader)} batches)")
    print(f"  Test Loader  : {len(y_test)} samples ({len(test_loader)} batches)")
    print(f"  TU-Berlin    : {len(tu_y)} samples ({len(tu_loader)} batches)")

    return train_loader, val_loader, test_loader, tu_loader, class_meta


def evaluate_model(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    num_classes: int = 50
) -> Dict[str, Any]:
    model.eval()
    criterion = nn.CrossEntropyLoss()
    total_loss = 0.0
    correct_top1 = 0
    correct_top5 = 0
    total = 0

    all_preds = []
    all_targets = []

    t0 = time.perf_counter()
    with torch.no_grad():
        for inputs, targets in loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            total_loss += loss.item() * targets.size(0)

            # Top-1
            _, pred_top1 = outputs.max(1)
            correct_top1 += pred_top1.eq(targets).sum().item()

            # Top-5
            _, pred_top5 = outputs.topk(5, dim=1, largest=True, sorted=True)
            correct_top5 += pred_top5.eq(targets.view(-1, 1).expand_as(pred_top5)).sum().item()

            total += targets.size(0)
            all_preds.extend(pred_top1.cpu().numpy().tolist())
            all_targets.extend(targets.cpu().numpy().tolist())

    latency_ms_per_sample = ((time.perf_counter() - t0) / total) * 1000.0

    top1_acc = (correct_top1 / total) * 100.0
    top5_acc = (correct_top5 / total) * 100.0
    avg_loss = total_loss / total

    precision, recall, f1, _ = precision_recall_fscore_support(
        all_targets, all_preds, average="macro", zero_division=0
    )

    return {
        "loss": round(avg_loss, 4),
        "top1_accuracy": round(top1_acc, 2),
        "top5_accuracy": round(top5_acc, 2),
        "macro_precision": round(float(precision), 4),
        "macro_recall": round(float(recall), 4),
        "macro_f1": round(float(f1), 4),
        "latency_ms": round(latency_ms_per_sample, 3),
        "predictions": all_preds,
        "targets": all_targets
    }


def train_architecture(
    model_name: str,
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    device: torch.device,
    max_epochs: int = 7,
    patience: int = 3
) -> Tuple[nn.Module, Dict[str, Any]]:
    print(f"\n=======================================================")
    print(f" TRAINING: {model_name}")
    print(f"=======================================================")
    
    model = model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max_epochs, eta_min=1e-5)
    criterion = nn.CrossEntropyLoss()
    scaler = torch.cuda.amp.GradScaler(enabled=(device.type == "cuda"))

    history = {
        "train_loss": [],
        "train_acc": [],
        "val_loss": [],
        "val_acc": [],
        "val_top5": [],
        "learning_rates": []
    }

    best_val_acc = 0.0
    best_state_dict = None
    epochs_no_improve = 0

    t_start = time.time()
    for epoch in range(1, max_epochs + 1):
        model.train()
        running_loss = 0.0
        running_correct = 0
        total_train = 0

        for inputs, targets in train_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()

            with torch.cuda.amp.autocast(enabled=(device.type == "cuda")):
                outputs = model(inputs)
                loss = criterion(outputs, targets)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item() * targets.size(0)
            _, preds = outputs.max(1)
            running_correct += preds.eq(targets).sum().item()
            total_train += targets.size(0)

        scheduler.step()
        train_loss = running_loss / total_train
        train_acc = (running_correct / total_train) * 100.0

        # Validation
        val_eval = evaluate_model(model, val_loader, device)

        current_lr = scheduler.get_last_lr()[0]
        history["train_loss"].append(round(train_loss, 4))
        history["train_acc"].append(round(train_acc, 2))
        history["val_loss"].append(val_eval["loss"])
        history["val_acc"].append(val_eval["top1_accuracy"])
        history["val_top5"].append(val_eval["top5_accuracy"])
        history["learning_rates"].append(round(current_lr, 6))

        print(f"Epoch [{epoch:02d}/{max_epochs:02d}] "
              f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
              f"Val Loss: {val_eval['loss']:.4f} | Val Acc: {val_eval['top1_accuracy']:.2f}% | "
              f"Val Top5: {val_eval['top5_accuracy']:.2f}% | LR: {current_lr:.6f}")

        # Check early stopping / save best
        if val_eval["top1_accuracy"] > best_val_acc:
            best_val_acc = val_eval["top1_accuracy"]
            best_state_dict = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"Early stopping triggered at epoch {epoch} (No improvement for {patience} epochs).")
                break

    training_time = time.time() - t_start
    print(f"Training completed in {training_time:.2f}s. Best Val Acc: {best_val_acc:.2f}%")

    # Restore best weights
    model.load_state_dict({k: v.to(device) for k, v in best_state_dict.items()})
    
    return model, {
        "model_name": model_name,
        "best_val_acc": best_val_acc,
        "training_time_sec": round(training_time, 2),
        "history": history
    }


def main():
    print("==================================================================")
    print(" SKETCH2SHAPE AI: COMPARATIVE MODEL TRAINING & EVALUATION BENCHMARK")
    print("==================================================================")

    device = setup_device()
    train_loader, val_loader, test_loader, tu_loader, class_meta = load_datasets()
    num_classes = class_meta["num_classes"]

    # 1. Instantiate both candidate architectures
    model_a = LightweightCNN(num_classes=num_classes)
    model_b = ResNet18Sketch(num_classes=num_classes)

    params_a = sum(p.numel() for p in model_a.parameters())
    params_b = sum(p.numel() for p in model_b.parameters())

    print(f"\nArchitecture A (Lightweight CNN) : {params_a:,} parameters")
    print(f"Architecture B (ResNet18-Adapted): {params_b:,} parameters")

    # 2. Train Architecture A
    trained_model_a, res_a = train_architecture(
        "Lightweight_CNN", model_a, train_loader, val_loader, device, max_epochs=7, patience=3
    )

    # 3. Train Architecture B
    trained_model_b, res_b = train_architecture(
        "ResNet18_Adapted", model_b, train_loader, val_loader, device, max_epochs=7, patience=3
    )

    # 4. Rigorous Evaluation on Test Set & External TU-Berlin Dataset
    print("\n=======================================================")
    print(" FINAL EVALUATION: TEST SET & EXTERNAL TU-BERLIN SET")
    print("=======================================================")

    test_eval_a = evaluate_model(trained_model_a, test_loader, device)
    tu_eval_a = evaluate_model(trained_model_a, tu_loader, device)

    test_eval_b = evaluate_model(trained_model_b, test_loader, device)
    tu_eval_b = evaluate_model(trained_model_b, tu_loader, device)

    print(f"\n--- [Model A: Lightweight CNN] ---")
    print(f"  Test Accuracy  : {test_eval_a['top1_accuracy']}% (Top-5: {test_eval_a['top5_accuracy']}%)")
    print(f"  Macro F1 Score : {test_eval_a['macro_f1']}")
    print(f"  TU-Berlin Eval : {tu_eval_a['top1_accuracy']}% (Top-5: {tu_eval_a['top5_accuracy']}%)")
    print(f"  Inference Speed: {test_eval_a['latency_ms']} ms/sample")

    print(f"\n--- [Model B: ResNet18-Adapted] ---")
    print(f"  Test Accuracy  : {test_eval_b['top1_accuracy']}% (Top-5: {test_eval_b['top5_accuracy']}%)")
    print(f"  Macro F1 Score : {test_eval_b['macro_f1']}")
    print(f"  TU-Berlin Eval : {tu_eval_b['top1_accuracy']}% (Top-5: {tu_eval_b['top5_accuracy']}%)")
    print(f"  Inference Speed: {test_eval_b['latency_ms']} ms/sample")

    # 5. Selection of Best Architecture
    # Primary selection criteria: Validation and Test Accuracy
    if test_eval_b["top1_accuracy"] >= test_eval_a["top1_accuracy"]:
        best_model_name = "ResNet18_Adapted"
        best_model = trained_model_b
        best_test_eval = test_eval_b
        best_tu_eval = tu_eval_b
        best_history = res_b["history"]
    else:
        best_model_name = "Lightweight_CNN"
        best_model = trained_model_a
        best_test_eval = test_eval_a
        best_tu_eval = tu_eval_a
        best_history = res_a["history"]

    print(f"\n>>> SELECTION WINNER: {best_model_name} (Top-1: {best_test_eval['top1_accuracy']}%, Top-5: {best_test_eval['top5_accuracy']}%)")

    # 6. Save Model Artifacts
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save best weights
    best_weights_path = MODELS_DIR / "best_model.pth"
    torch.save(best_model.state_dict(), best_weights_path)
    model_size_mb = best_weights_path.stat().st_size / (1024 * 1024)

    # Save model config
    config = {
        "model_version": "1.0.0",
        "selected_architecture": best_model_name,
        "input_shape": [1, 128, 128],
        "in_channels": 1,
        "num_classes": num_classes,
        "device": str(device),
        "model_size_mb": round(model_size_mb, 2),
        "inference_latency_ms": best_test_eval["latency_ms"],
        "class_names": class_meta["target_categories"]
    }
    with open(MODELS_DIR / "model_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    # Save training history
    with open(MODELS_DIR / "training_history.json", "w", encoding="utf-8") as f:
        json.dump({
            "Lightweight_CNN": res_a["history"],
            "ResNet18_Adapted": res_b["history"]
        }, f, indent=2)

    # Save comprehensive evaluation metrics
    eval_metrics = {
        "best_architecture": best_model_name,
        "quickdraw_test_metrics": {
            "top1_accuracy": best_test_eval["top1_accuracy"],
            "top5_accuracy": best_test_eval["top5_accuracy"],
            "macro_precision": best_test_eval["macro_precision"],
            "macro_recall": best_test_eval["macro_recall"],
            "macro_f1": best_test_eval["macro_f1"],
            "latency_ms": best_test_eval["latency_ms"]
        },
        "tu_berlin_external_metrics": {
            "top1_accuracy": best_tu_eval["top1_accuracy"],
            "top5_accuracy": best_tu_eval["top5_accuracy"],
            "macro_precision": best_tu_eval["macro_precision"],
            "macro_recall": best_tu_eval["macro_recall"],
            "macro_f1": best_tu_eval["macro_f1"]
        }
    }
    with open(MODELS_DIR / "evaluation_metrics.json", "w", encoding="utf-8") as f:
        json.dump(eval_metrics, f, indent=2)

    # Save model comparison summary
    comparison = {
        "Lightweight_CNN": {
            "parameters": params_a,
            "training_time_sec": res_a["training_time_sec"],
            "test_top1_acc": test_eval_a["top1_accuracy"],
            "test_top5_acc": test_eval_a["top5_accuracy"],
            "macro_f1": test_eval_a["macro_f1"],
            "tu_berlin_acc": tu_eval_a["top1_accuracy"],
            "tu_berlin_top5": tu_eval_a["top5_accuracy"],
            "latency_ms": test_eval_a["latency_ms"]
        },
        "ResNet18_Adapted": {
            "parameters": params_b,
            "training_time_sec": res_b["training_time_sec"],
            "test_top1_acc": test_eval_b["top1_accuracy"],
            "test_top5_acc": test_eval_b["top5_accuracy"],
            "macro_f1": test_eval_b["macro_f1"],
            "tu_berlin_acc": tu_eval_b["top1_accuracy"],
            "tu_berlin_top5": tu_eval_b["top5_accuracy"],
            "latency_ms": test_eval_b["latency_ms"]
        }
    }
    with open(MODELS_DIR / "model_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)

    # 7. Generate & Save Confusion Matrix Plot
    print("\nGenerating confusion matrix plot for best model...")
    cm = confusion_matrix(best_test_eval["targets"], best_test_eval["predictions"])
    
    plt.figure(figsize=(14, 12))
    plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title(f"Confusion Matrix ({best_model_name} on QuickDraw Test Split)", fontsize=14)
    plt.colorbar()
    
    tick_marks = np.arange(len(class_meta["target_categories"]))
    plt.xticks(tick_marks, class_meta["target_categories"], rotation=90, fontsize=7)
    plt.yticks(tick_marks, class_meta["target_categories"], fontsize=7)
    plt.ylabel("Ground Truth Class")
    plt.xlabel("Predicted Class")
    plt.tight_layout()
    
    cm_path = MODELS_DIR / "confusion_matrix.png"
    plt.savefig(cm_path, dpi=200)
    plt.close()
    print(f"Confusion matrix plot saved to: {cm_path}")

    # Copy experiment logs to experiments/
    with open(EXPERIMENTS_DIR / "training_run_summary.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "config": config,
            "comparison": comparison,
            "metrics": eval_metrics
        }, f, indent=2)

    print("\nAll training, evaluation, comparison, and confusion matrix artifacts saved successfully!")


if __name__ == "__main__":
    main()
