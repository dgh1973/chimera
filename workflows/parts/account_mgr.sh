#!/bin/sh
# DGH 2013.10.01
#
#
#
OLD_IFS=$IFS
NEW_IFS=,
user=$1
comment="$2"
groups=$3
check_return (){

    retval=$1
    if [ $retval -gt 0 ] ; then
        printf "FAILURE $2\n"
    else
        printf "SUCCESS $2\n"
    fi
}

# create user, if this fails it's probably because it already exists
# if it does, don't bother with a password change (that will mess people up)
printf "`uname -n`\n\n"
exists="0"
useradd -m -c "${comment}" $user
useradd_retval=$?
if [ $useradd_retval -ne 0 ] ; then
    exists="1"
fi
check_return $useradd_retval "creating $user"
if [ $exists -eq 0 ] ; then
    tail -1 $0 | passwd --stdin $user
    check_return $? "setting password for $user"
else
    printf "skipping password change for existing user $user\n"
fi

# assign groups in a cumulative manner
if [ x${groups} != "x" ] ; then
    IFS=$NEW_IFS
    for group in $groups ; do
        usermod -a -G $group $user
        check_return $? "adding $user to $group"
    done
    IFS=$OLD_IFS
fi

# set aging policy and remove outself upon exit
chage -m 0 -M 45 -W 14 -d 0 $user
check_return $? "setting password aging policy $user"
rm -f $0
exit 0


# the last line is the desired password

P@55W0rd!
