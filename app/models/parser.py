from .. import db
from .models import Cover, Transaction, StakingTransaction, NXMTransaction
from .utils import *
from datetime import datetime, timedelta
import json
import os
import requests
import textwrap

def get_event_logs(table, address, topic0):
  module = 'logs'
  action = 'getLogs'
  fromBlock = 1 if table is None else get_latest_block_number(table) + 1
  toBlock = 'latest'
  url = 'https://api.etherscan.io/api?' + \
        'module=%s&action=%s&fromBlock=%s&toBlock=%s&address=%s&topic0=%s&apikey=%s' \
        % (module, action, fromBlock, toBlock, address, topic0, os.environ['ETHERSCAN_API_KEY'])
  return json.loads(requests.get(url).text)['result']

def parse_mcr_event_logs():
  address = '0x2ec5d566bd104e01790b13de33fd51876d57c495'
  topic0 = '0xe4d7c0f9c1462bca57d9d1c2ec3a19d83c4781ceaf9a37a0f15dc55a6b43de4d'
  event = get_event_logs(None, address, topic0)[-1] # TODO historical MCR
  data = textwrap.wrap(event['data'][2:], 64)
  set_minimum_capital_requirement(int(data[3], 16) / 10**18)

def parse_cover_event_logs():
  address = '0x1776651F58a17a50098d31ba3C3cD259C1903f7A'
  topic0 = '0x535c0318711210e1ce39e443c5948dd7fa396c2774d0949812fcb74800e22730'
  for event in get_event_logs(Cover, address, topic0):
    data = textwrap.wrap(event['data'][2:], 64)
    db.session.add(Cover(
      block_number=int(event['blockNumber'], 16),
      cover_id=int(event['topics'][1], 16),
      contract_name=address_to_contract_name(data[0][-40:]),
      amount=float(int(data[1], 16)),
      currency='ETH' if data[-1].startswith('455448') else 'DAI',
      start_time=datetime.fromtimestamp(int(event['timeStamp'], 16)),
      end_time=datetime.fromtimestamp(int(data[2], 16))
    ))
    db.session.commit()

def parse_nxm_event_logs():
  address = '0xd7c49cee7e9188cca6ad8ff264c1da2e69d4cf3b'
  topic0 = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
  for event in get_event_logs(NXMTransaction, address, topic0):
    db.session.add(NXMTransaction(
      id=get_last_id(NXMTransaction) + 1,
      block_number=int(event['blockNumber'], 16),
      timestamp=datetime.fromtimestamp(int(event['timeStamp'], 16)),
      from_address='0x' + event['topics'][1][-40:],
      to_address='0x' + event['topics'][2][-40:],
      amount=int(event['data'], 16) / 10**18
    ))
    db.session.commit()

def parse_transactions(txns, address, symbol):
  for txn in txns:
    if 'isError' not in txn or txn['isError'] == '0':
      amount = float(txn['value']) / 10**18
      if txn['from'].lower() == address.lower():
        amount = -amount

      if amount != 0:
        timestamp = datetime.fromtimestamp(int(txn['timeStamp']))
        db.session.add(Transaction(
          id=get_last_id(Transaction) + 1,
          block_number=txn['blockNumber'],
          timestamp=timestamp,
          from_address=txn['from'],
          to_address=txn['to'],
          amount=amount,
          currency=symbol
        ))
        db.session.commit()

def build_transaction_url(address, startblock):
  module = 'account'
  action = 'txlist'
  endblock = 'latest'
  sort = 'asc'
  return 'https://api.etherscan.io/api?' + \
         'module=%s&action=%s&address=%s&startblock=%s&endblock=%s&sort=%s&apikey=%s' \
         % (module, action, address, startblock, endblock, sort, os.environ['ETHERSCAN_API_KEY'])

def parse_eth_transactions(startblock):
  address = '0xfD61352232157815cF7B71045557192Bf0CE1884'
  url = build_transaction_url(address, startblock)
  parse_transactions(json.loads(requests.get(url).text)['result'], address, 'ETH')
  url = url.replace('txlist', 'txlistinternal')
  parse_transactions(json.loads(requests.get(url).text)['result'], address, 'ETH')

def parse_dai_transactions(startblock):
  module = 'account'
  action = 'tokentx'
  contractaddress = '0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359'
  address = '0xfD61352232157815cF7B71045557192Bf0CE1884'
  endblock = 'latest'
  sort = 'asc'
  url = ('https://api.etherscan.io/api?module=%s&action=%s&contractaddress=%s&address=%s&' + \
        'startblock=%s&endblock=%s&sort=%s&apikey=%s') \
        % (module, action, contractaddress, address,
        startblock, endblock, sort, os.environ['ETHERSCAN_API_KEY'])
  parse_transactions(json.loads(requests.get(url).text)['result'], address, 'DAI')

def parse_staking_transactions():
  startblock = get_latest_block_number(StakingTransaction) + 1
  url = build_transaction_url('0xDF50A17bF58dea5039B73683a51c4026F3c7224E', startblock)
  for txn in json.loads(requests.get(url).text)['result']:
    if txn['isError'] == '0':
      data = textwrap.wrap(txn['input'][10:], 64)
      if len(data) == 2:
        start_time = datetime.fromtimestamp(int(txn['timeStamp']))
        db.session.add(StakingTransaction(
          id=get_last_id(StakingTransaction) + 1,
          block_number=txn['blockNumber'],
          start_time=start_time,
          end_time=start_time + timedelta(days=250),
          contract_name=address_to_contract_name(data[0][-40:]),
          amount=float(int(data[1], 16)) / 10**18
        ))
        db.session.commit()

def parse_etherscan_data():
  set_current_crypto_prices()
  parse_mcr_event_logs()
  parse_cover_event_logs()
  parse_nxm_event_logs()

  startblock = get_latest_block_number(Transaction) + 1
  parse_eth_transactions(startblock)
  parse_dai_transactions(startblock)
  parse_staking_transactions()
