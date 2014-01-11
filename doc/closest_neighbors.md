This is an idea for a way to do correlations.

For an indexed field, you can pretty quickly find the closest neighbors to any number by using mysql's min() and max() querys. Let's say our number is 26964706.452:

    mysql> select min(time_sec1) from obs_general where time_sec1  >= 26964706.452 and instrument_id = 'COISS';

    +----------------+
    | min(time_sec1) |
    +----------------+
    |   26964706.452 |
    +----------------+
    1 row in set (0.27 sec)

    mysql> select max(time_sec1) from obs_general where time_sec1  <=  26964706.452 and instrument_id = 'COISS';
    +----------------+
    | max(time_sec1) |
    +----------------+
    |   26964706.452 |
    +----------------+
    1 row in set (0.06 sec)

Then you can either pick bt the 2 results or use them both. (thx <http://stackoverflow.com/questions/1634725/select-closest-numerical-value-with-mysql-query>)

That was pretty fast. In this example, you could do 5 at a time in 1.35 seconds.. OPUS pages default to 100 per page but you could chunk the ajax calls.. there may be server side optimizations as well..

So let's say you have a result set filled with COISS images, and for each image you wanted to find the closest neighbor by start_time in the COVIMS dataset:

a script would look something like:

    def nearest_neighbors(time_sec1, instrument_id):
            next_lowest =
            select min(time_sec1) from obs_general
            where time_sec1  >= 28197007.975
            and instrument_id = 'COVIMS';

            next_highest =
            select max(time_sec1) from obs_general
            where time_sec1  <= 28197007.975
            and instrument_id = 'COVIMS';

            return next_lowest, next_highest

    # query to get the subset (obs_general joined
    # with cache_test) or maybe the client
    # sends 5 obs_general_nos at a time or something
    # then loop through them:

    while rows:

        # and just have to do the 2 querys:
        next_lowest, next_highest = nearest_neighbors()

        # if you want to go one neighbor further out, do n^2 more queries
        next_next_lowest, next_next_highest = nearest_neighbors(next_lowest)
        next_next_lowest, next_next_highest = nearest_neighbors(next_highest)


<b>To test this:</b>

    create a test cache table like cache_test;

    create table cache_test like *any other cache table*;

    insert into cache_test select obs_general_no from obs_general where instrument_id = 'COISS';


