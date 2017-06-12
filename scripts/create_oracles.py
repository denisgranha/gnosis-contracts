from web3 import Web3, KeepAliveRPCProvider, HTTPProvider
import json

port = 4001
host = 'localhost'


class Contract(object):

    def __init__(self, port, host):
        self.web3 = Web3(HTTPProvider(endpoint_uri='http://' + host + ':' + str(port)))
        self.centralized_oracle_factory_address = None
        self.collateral_token_address = None
        self.ether_token_address = None
        self.event_factory_address = None
        self.market_factory_address = None
        self.market_maker_address = None
        self.centralized_oracle_factory_abi = None
        self.centralized_oracle_abi = None
        self.event_factory_abi = None
        self.market_factory_abi = None
        self.market_maker_abi = None
        self.ether_token_abi = None
        self.categorical_event_abi = None

    def filter_callback(self, *args):
        for a in args:
            tx = self.web3.eth.getTransaction(a)
            print tx

    def set_contracts_variables(self):
        # read contracts addresses.
        contracts_file = open("../contracts/contracts.json","r")
        text = contracts_file.read()
        contracts_file.close()
        contracts_dict = json.loads(text)
        # set variables
        self.centralized_oracle_factory_address = contracts_dict.get('CentralizedOracleFactory')
        self.ether_token_address = contracts_dict.get('EtherToken')
        self.event_factory_address = contracts_dict.get('EventFactory')
        self.market_factory_address = contracts_dict.get('StandardMarketFactory')
        self.market_maker_address = contracts_dict.get('LMSRMarketMaker')

        with open('../contracts/abi/CategoricalEvent.json') as f:
            self.categorical_event_abi = json.load(f)

        with open('../contracts/abi/CentralizedOracleFactory.json') as f:
            self.centralized_oracle_factory_abi = json.load(f)

        with open('../contracts/abi/CentralizedOracle.json') as f:
            self.centralized_oracle_abi = json.load(f)

        with open('../contracts/abi/StandardMarketFactory.json') as f:
            self.market_factory_abi = json.load(f)

        with open('../contracts/abi/StandardMarket.json') as f:
            self.market_maker_abi = json.load(f)

        with open('../contracts/abi/EtherToken.json') as f:
            self.ether_token_abi = json.load(f)

        with open('../contracts/abi/EventFactory.json') as f:
            self.event_factory_abi = json.load(f)

    def start(self):
        """Creates markets and events"""

        tx_data = {'from': self.web3.eth.accounts[0], 'gas': 3000000}

        # set variables
        self.set_contracts_variables()

        # create oracle factory
        centralized_oracle_factory = self.web3.eth.contract(self.centralized_oracle_factory_address, abi=self.centralized_oracle_factory_abi)

        # create centralized oracle
        centralized_oracle_address = centralized_oracle_factory.call(tx_data).createCentralizedOracle('{:046d}'.format(46))

        # create event
        event_factory = self.web3.eth.contract(self.event_factory_address, abi=self.event_factory_abi)
        categorical_event_address = event_factory.call(tx_data).createCategoricalEvent(self.ether_token_address, centralized_oracle_address, 3)
        scalar_event_address = event_factory.call(tx_data).createScalarEvent(self.ether_token_address, centralized_oracle_address, 1, 2)

        market_factory = self.web3.eth.contract(self.market_factory_address, abi=self.market_factory_abi)
        market_address = market_factory.call(tx_data).createMarket(
            categorical_event_address,
            self.market_maker_address,
            10
        )

        # buy tokens
        ether_token = self.web3.eth.contract(self.ether_token_address, abi=self.ether_token_abi)
        ether_token.call(tx_data.copy().update({'value': 100000000000000000})).deposit()
        # buy shares
        market_maker = self.web3.eth.contract(market_address, abi=self.market_maker_abi)
        tx = market_maker.transact(tx_data).buy(
            1,
            1,
            10
        )

        centralized_oracle = self.web3.eth.contract(centralized_oracle_address, abi=self.centralized_oracle_abi)
        # set outcome
        centralized_oracle.transact(tx_data).setOutcome(1)

        categorical_event = self.web3.eth.contract(categorical_event_address, abi=self.categorical_event_abi)
        categorical_event.transact(tx_data).redeemWinnings()



# new_transaction_filter = web3.eth.filter('pending')
# new_transaction_filter.watch(filter_callback)

if __name__=='__main__':
    contract = Contract(port, host)
    contract.start()


