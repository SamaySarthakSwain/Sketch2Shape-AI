"""
Neural Network Architectures for Sketch Intelligence & Semantic Recognition
Architecture A: Lightweight Custom CNN (Fast, Low Parameter Count)
Architecture B: ResNet18 adapted for 1-channel (128x128) Grayscale Sketch Recognition
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models


class LightweightCNN(nn.Module):
    """
    Lightweight 4-stage convolutional neural network optimized for fast sketch recognition
    with minimal memory and computational overhead.
    """
    def __init__(self, num_classes: int = 50, in_channels: int = 1):
        super(LightweightCNN, self).__init__()
        self.num_classes = num_classes
        
        # Stage 1: 128x128 -> 64x64
        self.block1 = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        # Stage 2: 64x64 -> 32x32
        self.block2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        # Stage 3: 32x32 -> 16x16
        self.block3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        # Stage 4: 16x16 -> 8x8
        self.block4 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        self.adaptive_pool = nn.AdaptiveAvgPool2d((2, 2))
        self.dropout = nn.Dropout(p=0.35)
        
        self.classifier = nn.Sequential(
            nn.Linear(256 * 2 * 2, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.25),
            nn.Linear(256, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.block1(x)
        out = self.block2(out)
        out = self.block3(out)
        out = self.block4(out)
        out = self.adaptive_pool(out)
        out = torch.flatten(out, 1)
        out = self.dropout(out)
        out = self.classifier(out)
        return out


class ResNet18Sketch(nn.Module):
    """
    Standard ResNet-18 adapted for single-channel (grayscale 128x128) sketch inputs.
    Features residual skip connections and deep feature representations.
    """
    def __init__(self, num_classes: int = 50, in_channels: int = 1, pretrained: bool = False):
        super(ResNet18Sketch, self).__init__()
        self.num_classes = num_classes
        
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        base_resnet = models.resnet18(weights=weights)
        
        # Adapt first conv layer for 1-channel grayscale input
        if in_channels != 3:
            self.conv1 = nn.Conv2d(
                in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False
            )
            if pretrained:
                # Average weights across RGB channels
                with torch.no_grad():
                    self.conv1.weight.data = base_resnet.conv1.weight.data.mean(dim=1, keepdim=True)
        else:
            self.conv1 = base_resnet.conv1

        self.bn1 = base_resnet.bn1
        self.relu = base_resnet.relu
        self.maxpool = base_resnet.maxpool
        self.layer1 = base_resnet.layer1
        self.layer2 = base_resnet.layer2
        self.layer3 = base_resnet.layer3
        self.layer4 = base_resnet.layer4
        self.avgpool = base_resnet.avgpool
        
        # Adapt output linear classification layer
        self.fc = nn.Linear(base_resnet.fc.in_features, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)
        return x


def get_model(architecture_name: str, num_classes: int = 50, in_channels: int = 1) -> nn.Module:
    """Factory helper to instantiate supported sketch intelligence architectures."""
    arch = architecture_name.lower().strip()
    if arch in ["lightweight_cnn", "custom_cnn", "lightweight"]:
        return LightweightCNN(num_classes=num_classes, in_channels=in_channels)
    elif arch in ["resnet18", "resnet18_sketch", "resnet18_adapted", "resnet"]:
        return ResNet18Sketch(num_classes=num_classes, in_channels=in_channels, pretrained=False)
    else:
        raise ValueError(f"Unknown architecture '{architecture_name}'. Supported: 'lightweight_cnn', 'resnet18_sketch'")
