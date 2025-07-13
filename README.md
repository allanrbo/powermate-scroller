# powermate-scroller

This script allows me to use my Griffin Powermate as a scroll device on Linux. I'm running Debian 12, but it should be fairly distro agnostic.

Installation:

```
sudo su
cp powermate-scroller.service /etc/systemd/system/
cp powermate-scroller.py /usr/local/sbin/
systemctl daemon-reload
systemctl enable powermate-scroller
systemctl start powermate-scroller
systemctl status powermate-scroller
```
