# printed-tasks

Requires USB forwarding to WSL:

```
> usbipd list
2-13   0b05:19af  AURA LED Controller, USB Input Device                         Not shared
> usbipd attach --wsl --busid=2-15
> usbipd detach --busid=2-15
```

Certain situations require detaching and re-attaching the USB device through an admin-enabled Powershell. If `gunicorn` ends abrubtly it can lock the receipt printer into a busy state.
