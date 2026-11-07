---
license: apache-2.0
pipeline_tag: text-to-video
library_name: diffusers
---

# FastVideo FastWan2.2-TI2V-5B-FullAttn-Diffusers Model
<p align="center">
  <img src="https://raw.githubusercontent.com/hao-ai-lab/FastVideo/main/assets/logo.png" width="200"/>
</p>
<div>
  <div align="center">
    <a href="https://github.com/hao-ai-lab/FastVideo" target="_blank">FastVideo Team</a>&emsp;
  </div>

  <div align="center">
    <a href="https://huggingface.co/papers/2505.13389">HF Paper (VSA)</a> | <a href="https://arxiv.org/pdf/2505.13389">arXiv Paper (VSA)</a> | 
    <a href="https://github.com/hao-ai-lab/FastVideo">Github</a> |
    <a href="https://hao-ai-lab.github.io/FastVideo">Project Page</a>
  </div>
</div>

## Online Demo
You can try our models [here](https://fastwan.fastvideo.org/)！

## Introduction
We're excited to introduce the **FastWan2.2 series**—a new line of models finetuned with our novel **Sparse-distill** strategy. This approach jointly integrates DMD and VSA in a single training process, combining the benefits of both **distillation** to shorten diffusion steps and **sparse attention** to reduce attention computations, enabling even faster video generation.

FastWan2.2-TI2V-5B-Full-Diffusers is built upon Wan-AI/Wan2.2-TI2V-5B-Diffusers. It supports efficient **3-step inference** and produces high-quality videos at 121×704×1280 resolution. For training, we used simulated forward for the generator model, making the process data-free. **The current FastWan2.2-TI2V-5B-Full-Diffusers model is trained using only DMD**.

---

## Model Overview

- 3-step inference is supported.
- Our model is trained on **121×704×1280** resolution, but it supports generating videos with **any resolution**.(quality may degrade)
- Finetuning and inference scripts are available in the [FastVideo](https://github.com/hao-ai-lab/FastVideo) repository:  
  - [1 Node/GPU debugging finetuning script](https://github.com/hao-ai-lab/FastVideo/blob/main/scripts/distill/v1_distill_dmd_wan.sh)
  - [Slurm training example script](https://github.com/hao-ai-lab/FastVideo/blob/main/examples/distill/Wan2.2-TI2V-5B-Diffusers/Data-free/distill_dmd_t2v_5B.sh)  
  - [Inference script](https://github.com/hao-ai-lab/FastVideo/blob/main/scripts/inference/v1_inference_wan_dmd.sh)
```python
num_gpus=1
export FASTVIDEO_ATTENTION_BACKEND=FLASH_ATTN
export MODEL_BASE=FastVideo/FastWan2.2-TI2V-5B-Full-Diffusers
# export MODEL_BASE=hunyuanvideo-community/HunyuanVideo
# You can either use --prompt or --prompt-txt, but not both.
fastvideo generate \
    --model-path $MODEL_BASE \
    --sp-size $num_gpus \
    --tp-size 1 \
    --num-gpus $num_gpus \
    --height 704 \
    --width 1280 \
    --num-frames 121 \
    --num-inference-steps 3 \
    --fps 24 \
    --prompt-txt assets/prompt.txt \
    --negative-prompt "Bright tones, overexposed, static, blurred details, subtitles, style, works, paintings, images, static, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background, three legs, many people in the background, walking backwards" \
    --seed 1024 \
    --output-path outputs_video_dmd/ \
    --dmd-denoising-steps "1000,757,522"
```
- Try it out on **FastVideo** — we support a wide range of GPUs from **H100** to **4090**, and also support **Mac** users!

### Training Infrastructure

Training was conducted on **8 nodes with 64 H200 GPUs** in total, using a `global batch size = 64`, and training runs for **3000 steps (~12 hours)**   

If you use the FastWan2.2-TI2V-5B-FullAttn-Diffusers model for your research, please cite our paper:
```
@article{zhang2025vsa,
  title={VSA: Faster Video Diffusion with Trainable Sparse Attention},
  author={Zhang, Peiyuan and Huang, Haofeng and Chen, Yongqi and Lin, Will and Liu, Zhengzhong and Stoica, Ion and Xing, Eric and Zhang, Hao},
  journal={arXiv preprint arXiv:2505.13389},
  year={2025}
}
@article{zhang2025fast,
  title={Fast video generation with sliding tile attention},
  author={Zhang, Peiyuan and Chen, Yongqi and Su, Runlong and Ding, Hangliang and Stoica, Ion and Liu, Zhengzhong and Zhang, Hao},
  journal={arXiv preprint arXiv:2502.04507},
  year={2025}
}
```