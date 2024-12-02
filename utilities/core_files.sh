#!/bin/sh
#
# Script for adding a "core" set of files to chimera for management
#

old_ifs=${IFS}
new_ifs="
"

files="/etc/passwd
/etc/shadow
/etc/pam.d/system-auth
/etc/sssd/sssd.conf
/etc/login.defs
/etc/default/useradd
/etc/group
/etc/hosts
/etc/motd
/etc/sudoers
/etc/fstab
/etc/ntp.conf
/etc/chrony.conf
/etc/resolv.conf
/etc/nsswitch.conf
/etc/sysconfig/network
/etc/modprobe.conf
/etc/multipath.conf
/etc/security/limits.conf
/etc/syslog.conf
/etc/rsyslog.conf
/etc/yum.conf
/etc/sysconfig/iptables
/etc/mail/sendmail.cf
/etc/postfix/main.cf
/var/spool/cron/root
/home/dan/.bash_profile
/home/danielh@www.nslc.org/.bash_profile
/root/scripts/dns_failover.sh"

IFS=${new_ifs}
for s in $(/opt/chimera/manage.py servers --show=all|cut -d, -f1); do
    for f in ${files} ; do
        /opt/chimera/manage.py files --add=${s}:${f}
        /opt/chimera/manage.py files --delta=${s}:${f} &
    done
done

# Because some of the files above may not exist on all servers...
echo "delete from files_file where content='';" | mysql chimera

# Set canonical files here...
#echo "update files_file set canonical='1' where path='/home/dan/.bash_profile';" | mysql chimera
#echo "update files_file set canonical='1' where path='/home/danielh@www.nslc.org/.bash_profile';" | mysql chimera

exit 0
