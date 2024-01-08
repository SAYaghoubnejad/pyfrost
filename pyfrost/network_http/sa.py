from typing import List, Dict
from .abstract import NodesInfo
import pyfrost
import logging
import json
import uuid
import aiohttp
import asyncio


async def post_request(url: str, data: Dict, timeout: int = 10):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, timeout=timeout) as response:
            try:
                return await response.json()
            except asyncio.TimeoutError:
                return {
                    'status': 'TIMEOUT',
                    'error': 'Communication timed out',
                }
            except Exception as e:
                return {
                    'status': 'ERROR',
                    'error': f'An exception occurred: {type(e).__name__}: {e}',
                }


class SA:
    def __init__(self, nodes_info: NodesInfo, default_timeout: int = 200) -> None:

        self.nodes_info: NodesInfo = nodes_info
        self.default_timeout = default_timeout

    async def request_nonces(self, party: List, number_of_nonces: int = 10):
        call_method = '/v1/generate-nonces'
        request_data = {
            'number_of_nonces': number_of_nonces,
        }
        node_info = [self.nodes_info.lookup_node(node_id) for node_id in party]
        urls = [f'http://{node["host"]}:{node["port"]}' +
                call_method for node in node_info]
        request_tasks = [post_request(
            url, request_data, self.default_timeout) for url in urls]
        responses = await asyncio.gather(*request_tasks)
        nonces_response = dict(zip(party, responses))

        logging.debug(
            f'Nonces dictionary response: \n{json.dumps(nonces_response, indent=4)}')
        return nonces_response

    async def request_signature(self, dkg_key: Dict, nonces_list: Dict,
                                sa_data: Dict, sign_party: List) -> Dict:
        call_method = '/v1/sign'
        if not set(sign_party).issubset(set(dkg_key['party'])):
            response = {
                'result': 'FAILED',
                'signatures': None
            }
            return response
        request_id = str(uuid.uuid4())
        request_data = {
            'request_id': request_id,
            'dkg_public_key': dkg_key['public_key'],
            'nonces_list': nonces_list,
            'data': sa_data
        }
        node_info = [self.nodes_info.lookup_node(
            node_id) for node_id in sign_party]
        urls = [f'http://{node["host"]}:{node["port"]}' +
                call_method for node in node_info]
        request_tasks = [post_request(
            url, request_data, self.default_timeout) for url in urls]
        responses = await asyncio.gather(*request_tasks)
        signatures = dict(zip(sign_party, responses))

        logging.debug(
            f'Signatures dictionary response: \n{json.dumps(signatures, indent=4)}')
        sample_result = []
        signs = []
        aggregated_public_nonces = []
        str_message = None
        for data in signatures.values():
            _hash = data.get('hash')
            _signature_data = data.get('signature_data')
            _aggregated_public_nonce = data.get(
                'signature_data', {}).get('aggregated_public_nonce')
            if _hash and str_message is None:
                str_message = _hash
                sample_result.append(data)
            if _signature_data:
                signs.append(_signature_data)
            if _aggregated_public_nonce:
                aggregated_public_nonces.append(_aggregated_public_nonce)

        response = {
            'result': 'SUCCESSFUL',
            'signatures': None
        }
        if not len(set(aggregated_public_nonces)) == 1:
            aggregated_public_nonce = pyfrost.aggregate_nonce(
                str_message, nonces_list, dkg_key['public_key'])
            aggregated_public_nonce = pyfrost.frost.pub_to_code(
                aggregated_public_nonce)
            for data in signatures.values():
                if data['signature_data']['aggregated_public_nonce'] != aggregated_public_nonce:
                    data['status'] = 'MALICIOUS'
                    response['result'] = 'FAILED'
        for data in signatures.values():
            if data['status'] == 'MALICIOUS':
                response['result'] = 'FAILED'
                break

        if response['result'] == 'FAILED':
            response = {
                'result': 'FAILED',
                'signatures': signatures
            }
            logging.info(f'Signature response: {response}')
            return response

        # TODO: Remove pub_to_code
        aggregated_public_nonce = pyfrost.frost.code_to_pub(
            aggregated_public_nonces[0])
        aggregated_sign = pyfrost.aggregate_signatures(
            str_message, signs, aggregated_public_nonce, dkg_key['public_key'])
        if pyfrost.frost.verify_group_signature(aggregated_sign):
            aggregated_sign['message_hash'] = aggregated_sign['message_hash'].hex()
            aggregated_sign['result'] = 'SUCCESSFUL'
            aggregated_sign['signature_data'] = sample_result
            aggregated_sign['request_id'] = request_id
            logging.info(
                f'Aggregated sign result: {aggregated_sign["result"]}')
        else:
            aggregated_sign['result'] = 'FAILED'
        return aggregated_sign
