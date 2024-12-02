#!/bin/sh
old_ifs=${IFS}
new_ifs="
"
cd /opt/chimera > /dev/null
./manage.py servers --show=all > servers.txt
IFS=${new_ifs}
for line in $(cat servers.txt); do
    s=$(echo ${line}|cut -d, -f1)
    ./manage.py workflows --run="Collect Server Data":${s}
done
IFS=${old_ifs}
/bin/rm -f servers.txt
cd - > /dev/null

