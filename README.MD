TODO : FILTER ALSO ON MPAGE BY CAPITAL, ENTREPRISE SIZE ETC CHECK JSON

To use this system:

Run python create_configs.py --all to create the initial configuration files
Run python main.py to process all configured sites
Or run python main.py --sites lockbit bashe to process specific sites


tor config :
a12@1 721 % cat  ~/.tor/torrc

SocksPort 9050
ControlPort 9051
CookieAuthentication 1
# Longer circuit timeout for onion services
CircuitBuildTimeout 60
# More aggressive circuit handling
LearnCircuitBuildTimeout 0
# Improve onion service performance
HiddenServiceStatistics 0
OptimisticData 1
a12@1 721 % tor -f ~/.tor/torrc



website: 
using version 4 of tailwind, conf in the globalcss !