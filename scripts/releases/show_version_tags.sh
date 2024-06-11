#!/usr/bin/env bash
versions=`git tag --list "v*"`
for version in $versions
do
    vdate=`git for-each-ref --format="%(taggerdate)" refs/tags/$version | awk '{ printf "%s %s %2s %s",$5,$2,$3,$4 }'`
    fullvmsg=`git tag -n1 | grep $version`
    vmsg=`python -c "import sys;print(' '.join(sys.argv[2:]))" $fullvmsg`
    printf "%-8s %-20s " "$version" "$vdate"
    echo $vmsg | awk -F'---' '
        { n = split($1,x," ")
          len = 30
          for(i=1;i<=n;i++){
            if(len+length(x[i])>=80){printf "\n                              "; len = 30}
            printf "%s ",x[i]
            len += 1+length(x[i])
          }
          printf "\n"
        }'
done
