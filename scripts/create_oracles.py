from web3 import Web3, KeepAliveRPCProvider, HTTPProvider
from datetime import datetime
import json
import click
import ipfsapi
from ethereum.utils import sha3
from eth_abi import decode_abi


class Contract(object):

    methods = {}

    def __init__(self, testrpc_host, testrpc_port, ipfs_host, ipfs_port, gas):
        self.web3 = Web3(HTTPProvider(endpoint_uri='http://' + testrpc_host + ':' + str(testrpc_port)))
        self.ipfs_api = ipfsapi.connect(ipfs_host, ipfs_port)
        self.gas = gas
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
        self.scalar_event_abi = None

    def filter_callback(self, *args):
        for a in args:
            tx = self.web3.eth.getTransaction(a)
            print tx

    @staticmethod
    def remove_prefix(data):
        if not isinstance(data, str):
            return data
        if data[0:2] == '0x':
            return data[2::]
        else:
            return data

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

        with open('../contracts/abi/ScalarEvent.json') as f:
            self.scalar_event_abi = json.load(f)

    def add_abi(self, abi):
        added = 0
        for item in abi:
            if item.get(u'name'):
                method_header = None
                if item.get(u'inputs'):
                    # Generate methodID and link it with the abi
                    method_header = "{}({})".format(item[u'name'],
                                                    ','.join(map(lambda input: input[u'type'], item[u'inputs'])))
                else:
                    method_header = "{}()".format(item[u'name'])

                print method_header
                method_id = sha3(method_header).encode('hex')
                self.methods[method_id] = item
                added += 1
        return added

    def get_address_from_logs(self, logs, event_name=None):
        decoded_logs = self.decode_logs(logs)
        if isinstance(decoded_logs, list) and len(decoded_logs) > 0:
            for item in decoded_logs[0].get('params'):
                if item.get('name') == event_name:
                    return item.get('value')
        return None

    def decode_logs(self, logs):
        decoded = []
        for log in logs:
            method_id = log[u'topics'][0][2:]
            if self.methods.get(method_id):
                method = self.methods[method_id]
                decoded_params = []
                data_i = 0
                topics_i = 1
                data_types = []

                # get param types from properties not indexed
                for param in method[u'inputs']:
                    if not param[u'indexed']:
                        data_types.append(param[u'type'])

                decoded_data = decode_abi(data_types, log[u'data'])

                for param in method[u'inputs']:
                    decoded_p = {
                        u'name': param[u'name']
                    }

                    if param[u'indexed']:
                        decoded_p[u'value'] = self.remove_prefix(log[u'topics'][topics_i])
                        topics_i += 1
                    else:
                        decoded_p[u'value'] = self.remove_prefix(decoded_data[data_i])
                        data_i += 1

                    if u'[]' in param[u'type']:
                        if u'int' in param[u'type']:
                            decoded_p[u'value'] = list([long(account) for account in decoded_p[u'value']])
                        elif u'address' in param[u'type']:
                            decoded_p[u'value'] = list([self.remove_prefix(account) for account in decoded_p[u'value']])
                        else:
                            decoded_p[u'value'] = list(decoded_p[u'value'])
                    elif u'int' in param[u'type']:
                        decoded_p[u'value'] = long(decoded_p[u'value'])
                    elif u'address' == param[u'type']:
                        address = self.remove_prefix(decoded_p[u'value'])
                        if len(address) == 20:
                            decoded_p[u'value'] = address
                        elif len(address) == 64:
                            decoded_p[u'value'] = decoded_p[u'value'][24::]

                    decoded_params.append(decoded_p)
                decoded.append({
                    u'params': decoded_params,
                    u'name': method[u'name'],
                    u'address': self.remove_prefix(log[u'address'])
                })

        return decoded

    def start(self):
        """Creates markets and events"""

        tx_data = {'from': self.web3.eth.accounts[0], 'gas': self.gas}

        # saving event_description to IPFS
        event_description_json = {
            'title':'Test title',
            'description': 'test long description',
            'resolution_date': datetime.now().isoformat(),
            'outcomes': ['YES', 'NO']
        }

        ipfs_hash = self.ipfs_api.add_json(event_description_json)

        # set variables
        self.set_contracts_variables()

        # create oracle factory
        centralized_oracle_factory = self.web3.eth.contract(self.centralized_oracle_factory_address, abi=self.centralized_oracle_factory_abi)

        # create centralized oracle
        centralized_oracle_tx = centralized_oracle_factory.transact(tx_data).createCentralizedOracle(ipfs_hash)
        tx_receipt = self.web3.eth.getTransactionReceipt(centralized_oracle_tx)
        self.add_abi(self.centralized_oracle_factory_abi)
        centralized_oracle_address = self.get_address_from_logs(tx_receipt.get('logs'), 'centralizedOracle')
        print "\n########################\n"
        # create categorical event
        tx_data['gas'] = 100000000
        event_factory = self.web3.eth.contract(self.event_factory_address, abi=self.event_factory_abi)
        categorical_event_tx = event_factory.transact(tx_data).createCategoricalEvent(self.ether_token_address, centralized_oracle_address, 3)
        tx_receipt = self.web3.eth.getTransactionReceipt(categorical_event_tx)
        self.add_abi(self.event_factory_abi)
        categorical_event_address = self.get_address_from_logs(tx_receipt.get('logs'), 'categoricalEvent')
        print categorical_event_address
        print tx_receipt.get('logs')
        if not categorical_event_address:
            exit(0)
        print "\n########################\n"
        # create scalar event
        scalar_event_tx = event_factory.transact(tx_data).createScalarEvent(self.ether_token_address, centralized_oracle_address, 1, 2)
        tx_receipt = self.web3.eth.getTransactionReceipt(scalar_event_tx)
        self.add_abi(self.scalar_event_abi)
        scalar_event_address = self.get_address_from_logs(tx_receipt.get('logs'), 'scalarEvent')
        print "\n########################\n"
        # create market
        market_factory = self.web3.eth.contract(self.market_factory_address, abi=self.market_factory_abi)
        market_tx = market_factory.transact(tx_data).createMarket(categorical_event_address, self.market_maker_address, 0)
        tx_receipt = self.web3.eth.getTransactionReceipt(market_tx)
        self.add_abi(self.market_factory_abi)
        market_address = self.get_address_from_logs(tx_receipt.get('logs'), 'market')
        print "\n########################\n"
        # buy tokens
        ether_token = self.web3.eth.contract(self.ether_token_address, abi=self.ether_token_abi)
        ether_token.transact(tx_data.copy().update({'value': 100000000000000000})).deposit()
        # print "\n########################\n"
        # buy shares
        # market_maker = self.web3.eth.contract(market_address, abi=self.market_maker_abi)
        # tx = market_maker.transact(tx_data).buy(
        #     1,
        #     1,
        #     10
        # )
        # print "\n########################\n"
        centralized_oracle = self.web3.eth.contract(centralized_oracle_address, abi=self.centralized_oracle_abi)
        # set outcome
        centralized_oracle.transact(tx_data).setOutcome(1)
        print "\n########################\n"
        # categorical_event = self.web3.eth.contract(categorical_event_address, abi=self.categorical_event_abi)
        # categorical_event.transact(tx_data).redeemWinnings()
        print "\n######### DONE ##########\n"


@click.command()
@click.option('--testrpc_host', default="localhost", help='Ethereum node host')
@click.option('--testrpc_port', default='8545', help='Ethereum node port')
@click.option('--ipfs_host', default='localhost', help='IPFS node host')
@click.option('--ipfs_port', default='5001', help='IPFS node port')
@click.option('--gas', default=4000000, help='Transaction gas')
def setup(testrpc_host, testrpc_port, ipfs_host, ipfs_port, gas):
    contract = Contract(testrpc_host, testrpc_port, ipfs_host, ipfs_port, gas)
    contract.start()


if __name__=='__main__':
    setup()
