from web3 import Web3, KeepAliveRPCProvider, HTTPProvider
import json


def create_centralized_oracle(oracle_factory_address, event_factory_address, collateral_token):
    oracle_factory_abi = None
    centralized_oracle_abi = None
    event_factory_abi = None

    tx_data = {'from': web3.eth.accounts[0], 'gas': 3000000}

    with open('../contracts/abi/CentralizedOracleFactory.json') as f:
        oracle_factory_abi = json.load(f)

    with open('../contracts/abi/CentralizedOracle.json') as f:
        centralized_oracle_abi = json.load(f)

    with open('../contracts/abi/EventFactory.json') as f:
        event_factory_abi = json.load(f)

    # create oracle factory
    oracle = web3.eth.contract(oracle_factory_address, abi=oracle_factory_abi)

    # create centralized oracle
    centralized_oracle = oracle.call(tx_data).createCentralizedOracle('{:046d}'.format(46))

    # create event
    event_factory = web3.eth.contract(event_factory_address, abi=event_factory_abi)
    event_address = event_factory.call(tx_data).createCategoricalEvent(collateral_token, oracle.address, 2)
    print event_address


port = 4001
host = 'localhost'
centralized_oracle_address = '0xca3f881ff5b6e0c388cd9717aa5127a089fb1363'
collateral_token_address = '0x15fdb1d1d083ae5593c7904285ed7f264e10dd3f'
event_factory_address = '0x7506a6f972ba15fdeee0a7820822dc57daf5a494'

web3 = Web3(HTTPProvider(endpoint_uri='http://' + host + ':' + str(port)))

create_centralized_oracle(centralized_oracle_address, event_factory_address, collateral_token_address)


