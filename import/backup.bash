if [ -z $1 ]
then
        echo "please enter your mysql password as the first argument"
        exit
fi

cd ~/dumps
mysqldump --opt opus > opus.sql -p$1
mysqldump --opt opus_old > opus_older.sql -p$1
mysql opus_old < opus.sql -p$1 -v
