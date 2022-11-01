# Tennis Simulation model

### 2.3 version

In this version, we focus on increasing the efficiency, with the idea that the program automatically obtains match of the day information for prediction and automatically generates analysis reports, resulting the code tour_forecast.py.

Some small adjustments have been applied, such as, we need players who use statictis from their match of tournament qulification should played at least 3 qulifications in his last 10-13 matches.

In the tournaments been predicted last serveral months, we get the accurary of from 68% to 74%, which isn't an excellent result for we can easily discover that some predictions are ridiculous. Fortunately, it is not totally a silly thing, with some dark horses can be predicted of high significance. This phenomenon spurs us to consider some improvement, such as cluster. Hope next version could get more satisfied result.

 

### 2.2 version

We made some adjustments to the model. For example, considering that a player's service level depends on the player's own service level, the opponent's return level, and random factors on the spot, they should be taken into consideration. But the weight of these factors varies from players. Before this, we adopted the relatively simple processing method of 50% each, and now we make a simple correction. We decide to simulate games based on the correlation of the data of serving and receiving in the data of the player's ten games. Of course, there is still space for improvement in our method of applying corrections, and the results are still not satisfing.
In addition, we have greatly expanded the database to include all ATP Tour qualifying data since 2022, which increase the predictability rate.



### 2.1 version

According to the problems we met in inserting data into SQL Server including missing by using http://ultimatetennisstatistics.com and http://sofascore.com/Tennis . We turn our sight to http://rank-tennis.com . Except for some error of Grand Slam in 2021, this website can provide sufficient data. Now we have aborted http://sofascore.com/Tennis for its difficulty in selecting data quickly.

We also polish up the code and the SQL structure in order to improve efficiency of forecasting matches consecutively.

**Files include:**

- match_result.py   simulate the match result for input players' name.
- match_info.py   record match result and statistics for input tournament information
- rank-tennis.py   record statistics of match which is lack in UTS from rank-tennis

### 2.0  version

We have applied SQL into our model. SQL can store the data and easily used into calculation without frequently crawling data from the web. The model itself doesn't have too much changes. We will introduce Dirichlet procession in the next version. We use SQL Server in the code.

Something important should be explained is that we are not support ML or DL which have been spread used in almost every field by scientists who even didn't think whether ML could follow the principle of the phenomenon. In that case, ML & DL which have lots of parameters to be optimized just act as the role of memorizer. We don't mean that ML & DL are useless, while we just emphasize that it is a method that constructs relationship of the points in the domain and can't escape from the category of regression.

**Files include:**

- match_result.py   simulate the match result for input players' name.
- match_info.py   record match result and statistics for input tournament information
- sofa.py   record statistics of match which is lack in UTS from SofaScore 



### 1.0  version

This is a very low and raw model for simulation of the result of the tennis game. Just according to the technical statistics of the players, we simulate a tennis game with the rule.  The statistics of the players used for this model should be related to the level of the opponent. For consideration of the random error, we use random disturbance term, but this should be adjusted by the type of the surface and the number of the sets has been finished. The value of the random disturbance term is decided by myself.

ATTENTION: The statistics of the player should be related with the surface, level of the opponent and includes: ACE, Double Fault, 1st serve in, 1st serve won, 2nd serve won, Break points save, 1st return won, 2nd return won, Break points convert, Elo of the surface. You can use more terms to improve it .

We have introduced variance method into this model. It is more reasonable.

With some samples to test, the results is generally convinced. We hope to make more large improvement in the future.  

**files include:**

- UTS_playerinfo.xls    Top 300 players' id
- tennissimulationmodel.py    model used for simulation, based on Gauss procession.