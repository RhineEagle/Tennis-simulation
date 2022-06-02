# Tennis Simulation model

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