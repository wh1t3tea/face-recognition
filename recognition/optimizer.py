from torch import optim
import torch
from torch.optim import lr_scheduler


def get_pretrain_param_groups(model, skip_list=(), skip_keywords=()):
    has_decay = []
    no_decay = []
    has_decay_name = []
    no_decay_name = []

    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        if len(param.shape) == 1 or name.endswith(".bias") or (name in skip_list) or \
                check_keywords_in_name(name, skip_keywords):
            no_decay.append(param)
            no_decay_name.append(name)
        else:
            has_decay.append(param)
            has_decay_name.append(name)
    return [{'params': has_decay},
            {'params': no_decay, 'weight_decay': 0.}]


def check_keywords_in_name(name, keywords=()):
    isin = False
    for keyword in keywords:
        if keyword in name:
            isin = True
    return isin


def get_optimizer(entities, cfg):
    """

    :param entities:
    :param cfg:
    :return:
    """
    params_bn = []
    params = []

    for entity in entities:
        _params = []
        _params_bn = []
        for name, param in entity.named_parameters():
            if not 'bn' in name:
                _params.append(param)
            else:
                _params_bn.append(param)
        params_bn.append(_params_bn)
        params.append(_params)
    bb_params, arc_params = params
    bb_params_bn, arc_params_bn = params_bn
    all_params = [{"params": bb_params},
                  {"params": arc_params},
                  {"params": bb_params_bn, "weight_decay": 0.},
                  {"params": arc_params_bn, "weight_decay": 0.}]

    if cfg.get("sgd", False):
        optim_cfg = cfg["sgd"]
        scheduler_cfg = optim_cfg["scheduler"]
        optimizer = optim.SGD(params=all_params,
                              lr=optim_cfg["base_lr"],
                              weight_decay=optim_cfg["weight_decay"],
                              momentum=optim_cfg["momentum"])
        scheduler = lr_scheduler.MultiStepLR(optimizer,
                                             scheduler_cfg["reduce_epochs"],
                                             scheduler_cfg["gamma"])

    elif cfg.get("adam", False):
        optim_cfg = cfg["adam"]
        scheduler_cfg = optim_cfg["scheduler"]
        optimizer = optim.Adam(params=all_params,
                               lr=optim_cfg["base_lr"],
                               weight_decay=optim_cfg["weight_decay"])
        scheduler = lr_scheduler.StepLR(optimizer,
                                        scheduler_cfg["step"],
                                        scheduler_cfg["gamma"])

    elif cfg.get("adamw", False):
        optim_cfg = cfg["adamw"]
        scheduler_cfg = optim_cfg["scheduler"]
        optimizer = optim.AdamW(params=all_params,
                                lr=optim_cfg["base_lr"],
                                weight_decay=optim_cfg["weight_decay"])
        scheduler = lr_scheduler.StepLR(optimizer,
                                        scheduler_cfg["step"],
                                        scheduler_cfg["gamma"])
    else:
        raise Exception("Unexpected optimizer. Choose available optimizer: 'sgd', 'adam', 'adamw'")
    return optimizer, scheduler