# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Tuple

import torchvision
from pytorch_lightning.utilities import _BOLTS_AVAILABLE
from pytorch_lightning.utilities.exceptions import MisconfigurationException
from torch import nn as nn

if _BOLTS_AVAILABLE:
    from pl_bolts.models.self_supervised import SimCLR, SwAV

ROOT_S3_BUCKET = "https://pl-bolts-weights.s3.us-east-2.amazonaws.com"

MOBILENET_MODELS = ["mobilenet_v2"]
VGG_MODELS = ["vgg11", "vgg13", "vgg16", "vgg19"]
RESNET_MODELS = ["resnet18", "resnet34", "resnet50", "resnet101", "resnet152", "resnext50_32x4d", "resnext101_32x8d"]
DENSENET_MODELS = ["densenet121", "densenet169", "densenet161"]
TORCHVISION_MODELS = MOBILENET_MODELS + VGG_MODELS + RESNET_MODELS + DENSENET_MODELS

BOLTS_MODELS = ["simclr-imagenet", "swav-imagenet"]


def backbone_and_num_features(model_name: str, *args, **kwargs) -> Tuple[nn.Module, int]:
    if model_name in BOLTS_MODELS:
        return bolts_backbone_and_num_features(model_name)

    if model_name in TORCHVISION_MODELS:
        return torchvision_backbone_and_num_features(model_name, *args, **kwargs)

    raise ValueError(f"{model_name} is not supported yet.")


def bolts_backbone_and_num_features(model_name: str) -> Tuple[nn.Module, int]:
    """
    >>> bolts_backbone_and_num_features('simclr-imagenet')  # doctest: +ELLIPSIS
    (Sequential(...), 2048)
    >>> bolts_backbone_and_num_features('swav-imagenet')  # doctest: +ELLIPSIS
    (Sequential(...), 3000)
    """

    # TODO: maybe we should plain pytorch weights so we don't need to rely on bolts to load these
    # also mabye just use torchhub for the ssl lib
    def load_simclr_imagenet(path_or_url: str = f"{ROOT_S3_BUCKET}/simclr/bolts_simclr_imagenet/simclr_imagenet.ckpt"):
        simclr = SimCLR.load_from_checkpoint(path_or_url, strict=False)
        # remove the last two layers & turn it into a Sequential model
        backbone = nn.Sequential(*list(simclr.encoder.children())[:-2])
        return backbone, 2048

    def load_swav_imagenet(path_or_url: str = f"{ROOT_S3_BUCKET}/swav/swav_imagenet/swav_imagenet.pth.tar"):
        swav = SwAV.load_from_checkpoint(path_or_url, strict=True)
        # remove the last two layers & turn it into a Sequential model
        backbone = nn.Sequential(*list(swav.model.children())[:-2])
        return backbone, 3000

    models = {
        'simclr-imagenet': load_simclr_imagenet,
        'swav-imagenet': load_swav_imagenet,
    }
    if not _BOLTS_AVAILABLE:
        raise MisconfigurationException("Bolts isn't installed. Please, use ``pip install lightning-bolts``.")
    if model_name in models:
        return models[model_name]()

    raise ValueError(f"{model_name} is not supported yet.")


def torchvision_backbone_and_num_features(model_name: str, pretrained: bool = True) -> Tuple[nn.Module, int]:
    """
    >>> torchvision_backbone_and_num_features('mobilenet_v2')  # doctest: +ELLIPSIS
    (Sequential(...), 1280)
    >>> torchvision_backbone_and_num_features('resnet18')  # doctest: +ELLIPSIS
    (Sequential(...), 512)
    >>> torchvision_backbone_and_num_features('densenet121')  # doctest: +ELLIPSIS
    (Sequential(...), 1024)
    """
    model = getattr(torchvision.models, model_name, None)
    if model is None:
        raise MisconfigurationException(f"{model_name} is not supported by torchvision")

    if model_name in MOBILENET_MODELS + VGG_MODELS:
        model = model(pretrained=pretrained)
        backbone = model.features
        num_features = model.classifier[-1].in_features
        return backbone, num_features

    elif model_name in RESNET_MODELS:
        model = model(pretrained=pretrained)
        # remove the last two layers & turn it into a Sequential model
        backbone = nn.Sequential(*list(model.children())[:-2])
        num_features = model.fc.in_features
        return backbone, num_features

    elif model_name in DENSENET_MODELS:
        model = model(pretrained=pretrained)
        backbone = nn.Sequential(*model.features, nn.ReLU(inplace=True))
        num_features = model.classifier.in_features
        return backbone, num_features

    raise ValueError(f"{model_name} is not supported yet.")
