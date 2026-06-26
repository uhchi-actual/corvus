# Docker WSL2 Disk Cap

The handoff calls out a previous WSL2 Docker VHDX growth issue. Before heavy
Docker work, cap WSL2 disk usage by adding this to `~/.wslconfig`:

```ini
[wsl2]
disk=40GB
```

Then restart WSL2:

```powershell
wsl --shutdown
```

Prune Docker regularly:

```bash
docker system prune -af --volumes
```

Keep the local model at `JOSIEFIED-Qwen3:8b Q5_K_M` or smaller on 8 GB VRAM.

