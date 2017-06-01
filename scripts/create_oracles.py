from web3 import Web3, KeepAliveRPCProvider, HTTPProvider
import json
import time

port = 4001
host = 'localhost'
centralized_oracle_factory_address = '0xca3f881ff5b6e0c388cd9717aa5127a089fb1363'
collateral_token_address = '0x15fdb1d1d083ae5593c7904285ed7f264e10dd3f'
ether_token_address = '0x15fdb1d1d083ae5593c7904285ed7f264e10dd3f'
event_factory_address = '0x7506a6f972ba15fdeee0a7820822dc57daf5a494'
market_factory_address = '0x2f2be9db638cb31d4143cbc1525b0e104f7ed597'
market_maker_address = '0x7050fde6c38137407904e004fffd6463a64b0cba'


def filter_callback(*args):
    for a in args:
        tx = web3.eth.getTransaction(a)
        print tx


def start(p_oracle_factory_address, p_event_factory_address, p_market_factory_address,
          p_collateral_token, p_market_maker_address, p_ether_token_address):
    """Creates events"""

    oracle_factory_abi = None
    centralized_oracle_abi = None
    event_factory_abi = None
    market_factory_abi = None
    market_maker_abi = None
    ether_token_abi = None
    categorical_event_abi = None

    tx_data = {'from': web3.eth.accounts[0], 'gas': 3000000}

    with open('../contracts/abi/CategoricalEvent.json') as f:
        categorical_event_abi = json.load(f)

    with open('../contracts/abi/CentralizedOracleFactory.json') as f:
        oracle_factory_abi = json.load(f)

    with open('../contracts/abi/CentralizedOracle.json') as f:
        centralized_oracle_abi = json.load(f)

    with open('../contracts/abi/DefaultMarketFactory.json') as f:
        market_factory_abi = json.load(f)

    with open('../contracts/abi/DefaultMarket.json') as f:
        market_maker_abi = json.load(f)

    with open('../contracts/abi/EtherToken.json') as f:
        ether_token_abi = json.load(f)

    with open('../contracts/abi/EventFactory.json') as f:
        event_factory_abi = json.load(f)

    # create oracle factory
    oracle = web3.eth.contract(p_oracle_factory_address, abi=oracle_factory_abi)

    # create centralized oracle
    centralized_oracle_address = oracle.call(tx_data).createCentralizedOracle('{:046d}'.format(46))

    # create event
    event_factory = web3.eth.contract(event_factory_address, abi=event_factory_abi)
    categorical_event_address = event_factory.call(tx_data).createCategoricalEvent(p_collateral_token, centralized_oracle_address, 3)
    scalar_event_address = event_factory.call(tx_data).createScalarEvent(p_collateral_token, centralized_oracle_address, 1, 2)

    market_factory = web3.eth.contract(market_factory_address, abi=market_factory_abi)
    market_address = market_factory.call(tx_data).createMarket(
        categorical_event_address,
        p_market_maker_address,
        10
    )

    # buy tokens
    ether_token = web3.eth.contract(p_ether_token_address, abi=ether_token_abi)
    ether_token.call(tx_data.copy().update({'value': 100000000000000000})).deposit()
    # buy shares
    market_maker = web3.eth.contract(market_address, abi=market_maker_abi)
    tx = market_maker.transact(tx_data).buy(
        1,
        1,
        10
    )

    centralized_oracle = web3.eth.contract(centralized_oracle_address, abi=centralized_oracle_abi)
    # set outcome
    centralized_oracle.transact(tx_data).setOutcome(1)

    categorical_event = web3.eth.contract(categorical_event_address, abi=categorical_event_abi)
    categorical_event.transact(tx_data).redeemWinnings()



web3 = Web3(HTTPProvider(endpoint_uri='http://' + host + ':' + str(port)))

# new_transaction_filter = web3.eth.filter('pending')
# new_transaction_filter.watch(filter_callback)

start(
    centralized_oracle_factory_address,
    event_factory_address,
    market_factory_address,
    collateral_token_address,
    market_maker_address,
    ether_token_address
)


