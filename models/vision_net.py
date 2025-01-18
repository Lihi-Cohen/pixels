import torch
import torch.nn as nn
import torch.nn.functional as F


class Resnet(nn.Module):
    def __init__(self, original_resnet):
        super(Resnet, self).__init__()
        self.features = nn.Sequential(
            *list(original_resnet.children())[:-1])
        # for param in self.features.parameters():
        # 	param.requires_grad = False

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), x.size(1))
        return x


class ResnetFC(nn.Module):
    def __init__(self, original_resnet, fc_dim=64,
                 pool_type='maxpool', conv_size=3):
        super(ResnetFC, self).__init__()
        self.pool_type = pool_type

        self.features = nn.Sequential(
            *list(original_resnet.children())[:-2])

        self.fc = nn.Conv2d(
            512, fc_dim, kernel_size=conv_size, padding=conv_size//2)

    def forward(self, x, pool=True):
        x = self.features(x)
        x = self.fc(x)

        if not pool:
            return x

        if self.pool_type == 'avgpool':
            x = F.adaptive_avg_pool2d(x, 1)
        elif self.pool_type == 'maxpool':
            x = F.adaptive_max_pool2d(x, 1)

        x = x.view(x.size(0), x.size(1))
        return x

    def forward_multiframe(self, x, pool=True):
        (B, C, T, H, W) = x.size()
        x = x.permute(0, 2, 1, 3, 4).contiguous()
        x = x.view(B*T, C, H, W)

        x = self.features(x)
        x = self.fc(x)

        (_, C, H, W) = x.size()
        x = x.view(B, T, C, H, W)
        x = x.permute(0, 2, 1, 3, 4)

        if not pool:
            return x

        if self.pool_type == 'avgpool':
            x = F.adaptive_avg_pool3d(x, 1)
        elif self.pool_type == 'maxpool':
            x = F.adaptive_max_pool3d(x, 1)

        x = x.view(B, C)
        return x


class ResnetDilated(nn.Module):
    def __init__(self, orig_resnet, fc_dim=64, pool_type='maxpool',
                 dilate_scale=16, conv_size=3):
        super(ResnetDilated, self).__init__()
        from functools import partial

        self.pool_type = pool_type

        if dilate_scale == 8:
            orig_resnet.layer3.apply(
                partial(self._nostride_dilate, dilate=2))
            orig_resnet.layer4.apply(
                partial(self._nostride_dilate, dilate=4))
        elif dilate_scale == 16:
            orig_resnet.layer4.apply(
                partial(self._nostride_dilate, dilate=2))

        self.features = nn.Sequential(
            *list(orig_resnet.children())[:-2])

        self.fc = nn.Conv2d(
            512, fc_dim, kernel_size=conv_size, padding=conv_size//2)

    def _nostride_dilate(self, m, dilate):
        classname = m.__class__.__name__
        if classname.find('Conv') != -1:
            # the convolution with stride
            if m.stride == (2, 2):
                m.stride = (1, 1)
                if m.kernel_size == (3, 3):
                    m.dilation = (dilate//2, dilate//2)
                    m.padding = (dilate//2, dilate//2)
            # other convoluions
            else:
                if m.kernel_size == (3, 3):
                    m.dilation = (dilate, dilate)
                    m.padding = (dilate, dilate)

    def forward(self, x, pool=True):
        x = self.features(x)
        x = self.fc(x)

        if not pool:
            return x

        if self.pool_type == 'avgpool':
            x = F.adaptive_avg_pool2d(x, 1)
        elif self.pool_type == 'maxpool':
            x = F.adaptive_max_pool2d(x, 1)

        x = x.view(x.size(0), x.size(1))
        return x

    def forward_multiframe(self, x, pool=True):
        x = torch.stack(x, dim=2)  # Stack along the time dimension
        x = x.squeeze(2)  # Remove redundent dimension of size 1
        if len(x.size()) != 5:
            raise ValueError(f"Input tensor has fewer or more than 5 dimensions : {x.size()}")
            
        (B, C, T, H, W) = x.size()
        x = x.permute(0, 2, 1, 3, 4).contiguous()
        x = x.view(B*T, C, H, W)

        x = self.features(x)
        x = self.fc(x)

        (_, C, H, W) = x.size()
        x = x.view(B, T, C, H, W)
        x = x.permute(0, 2, 1, 3, 4)

        if not pool:
            return x

        if self.pool_type == 'avgpool':
            x = F.adaptive_avg_pool3d(x, 1)
        elif self.pool_type == 'maxpool':
            x = F.adaptive_max_pool3d(x, 1)

        x = x.view(B, C)
        return x
        
class Vit(nn.Module):
    def __init__(self, vit_model_name="google/vit-base-patch16-224-in21k", patch_size=16, 
                 feature_dim=64, frame_size=(224, 224), pool_type='maxpool'):
        super(VideoFeatureExtractorBatch, self).__init__()
        self.patch_size = patch_size
        self.frame_size = frame_size
        self.pool_type = pool_type

        self.vit = ViTModel.from_pretrained(vit_model_name)
        self.feature_projector = nn.Linear(self.vit.config.hidden_size, feature_dim)

    def forward(self, x, pool=True):
        """
        Args:
            video_frames: Tensor of shape (B, C, T, H, W)
            Returns:
                - If pool=True: Tensor of shape (B, C)
                - If pool=False: Tensor of shape (B, C, H, W)
        """
        B, C, T, H, W = x.size()
        assert (H, W) == self.frame_size, "Input frames must match the initialized frame size"
        
        x = x.permute(0, 2, 1, 3, 4).contiguous()
    
        # Combine batch and temporal dimensions for batch processing
        x = x.view(B * T, C, H, W)  # Shape: (B * T, C, H, W)
    
        # Pass all frames through the shared ViT backbone
        x = self.vit(pixel_values=x).last_hidden_state  # Shape: (B * T, num_patches, hidden_size)
    
        # Project ViT features to desired feature dimension
        x = self.feature_projector(x)  # Shape: (B * T, num_patches, C)
    
        # Reshape patches back to spatial dimensions (H // patch_size, W // patch_size)
        num_patches_h = H // self.patch_size
        num_patches_w = W // self.patch_size
        x = x.view(B, T, num_patches_h, num_patches_w, -1)
    
        if pool:
            # Temporal pooling (max or avg)
            if self.pool_type == 'avgpool':
                x = torch.mean(x, dim=1)  # Shape: (B, H // patch_size, W // patch_size, C)
            elif self.pool_type == 'maxpool':
                x = torch.max(x, dim=1).values  # Shape: (B, H // patch_size, W // patch_size, feature_dim)
    
            # Adaptive pooling to (1, 1) to match final Resnet output
            x = nn.functional.adaptive_avg_pool2d(
                x.permute(0, 3, 1, 2), output_size=1
            ).squeeze(-1).squeeze(-1)  # Shape: (B, C)
            return x
        else:
            # Upsample patches to match the original image size (H, W)
            x = nn.functional.interpolate(
                x.permute(0, 1, 4, 2, 3),  # Shape: (B, T, C, num_patches_h, num_patches_w)
                size=(H, W),  # Upsample to original image size
                mode='bilinear',
                align_corners=False,
            ).permute(0, 2, 1, 3, 4)  # Shape: (B, C, T, H, W)
    
            # Return the per-frame features for each channel
            return x
