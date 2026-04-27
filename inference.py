import os
from dotenv import load_dotenv

load_dotenv()

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
from enum import Enum
import timm
from transformers import AutoModel
from peft import LoraConfig, get_peft_model, PeftModel

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using: {DEVICE}")

CKPT_PATH = r"C:\Users\krmcd\OneDrive\Desktop\Projects\GeoGuessr_Bot\models\phase3\phase3_best.pth"
LORA_PATH = r"C:\Users\krmcd\OneDrive\Desktop\Projects\GeoGuessr_Bot\models\phase3\phase3_lora_adapter"
IMG_SIZE  = 336


class VisionBackbone(str, Enum):
    DINO_V3_SMALL = 'dinov3-vits16-pretrain-lvd1689m'
    DINO_V3_BASE  = 'dinov3-vitb16-pretrain-lvd1689m'
    DINO_V3_LARGE = 'dinov3-vitl16-pretrain-lvd1689m'

class SwinBrain(str, Enum):
    SWIN_TINY  = 'swin_tiny_patch4_window7_224'
    SWIN_SMALL = 'swin_small_patch4_window7_224'
    SWIN_BASE  = 'swin_base_patch4_window7_224'

class DualHeadGeoGuessr(nn.Module):
    def __init__(self, img_size, num_classes, vision_backbone=VisionBackbone.DINO_V3_SMALL, swin_brain=SwinBrain.SWIN_TINY):
        super().__init__()

        model_id = f"facebook/{vision_backbone.value}"
        self.dino = AutoModel.from_pretrained(model_id, attn_implementation="eager")
        for param in self.dino.parameters():
            param.requires_grad = False
        lora_config = LoraConfig(r=16, lora_alpha=32, target_modules="all-linear", bias="none")
        self.dino = get_peft_model(self.dino, lora_config)

        self.swin = timm.create_model(swin_brain.value, pretrained=False, num_classes=num_classes, img_size=img_size)
        old_conv = self.swin.patch_embed.proj
        self.swin.patch_embed.proj = nn.Conv2d(4, old_conv.out_channels, kernel_size=4, stride=4)

        in_features = self.swin.head.fc.in_features
        self.swin.head.fc = nn.Identity()
        self.country_tail = nn.Linear(in_features, num_classes)
        self.coord_tail   = nn.Linear(in_features, 2)

    def forward(self, x):
        with torch.no_grad():
            outputs = self.dino(x.float(), output_attentions=True)
        last_layer_attn = outputs.attentions[-1]
        mean_attn = last_layer_attn.mean(dim=1)
        patch_size = 16
        grid_h, grid_w = x.shape[2] // patch_size, x.shape[3] // patch_size
        num_patches = grid_h * grid_w
        cls_attn = mean_attn[:, 0, -num_patches:]
        heatmap = cls_attn.reshape(x.shape[0], 1, grid_h, grid_w)
        heatmap = F.interpolate(heatmap, size=(x.shape[2], x.shape[3]), mode='bilinear')
        h_mean = heatmap.mean(dim=(2, 3), keepdim=True)
        h_std = heatmap.std(dim=(2, 3), keepdim=True)
        heatmap = (heatmap - h_mean) / (h_std + 1e-6)
        x_4ch = torch.cat([x, heatmap], dim=1)
        features = self.swin(x_4ch)
        return self.coord_tail(features)

model = None

def init_model():
    global model
    if model is not None:
        return
        
    ckpt = torch.load(CKPT_PATH, map_location='cpu')
    num_classes = ckpt['country_tail']['weight'].shape[0]
    
    model = DualHeadGeoGuessr(img_size=IMG_SIZE, num_classes=num_classes)
    model.swin.load_state_dict(ckpt['swin'])
    model.country_tail.load_state_dict(ckpt['country_tail'])
    model.coord_tail.load_state_dict(ckpt['coord_tail'])
    model.dino = PeftModel.from_pretrained(model.dino.base_model.model, LORA_PATH)
    model = model.to(DEVICE)
    model.eval()
    print("Model loaded")

LAT_SCALE = torch.tensor(90.0)
LON_SCALE = torch.tensor(180.0)
SCALE = torch.stack([LAT_SCALE, LON_SCALE])

def denormalise_coords(norm):
    return norm * SCALE.to(norm.device)

transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def predict_coordinates(image_path):
    img = Image.open(image_path).convert('RGB')
    tensor = transform(img).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        pred_coords_n = model(tensor)

    coords = denormalise_coords(pred_coords_n.squeeze(0))
    lat, lon = coords[0].item(), coords[1].item()

    print(f"Predicted coords: {lat:.4f}, {lon:.4f}")
    return lat, lon


