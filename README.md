# PyFrost

PyFrost is a Python implementation of the [FROST](https://eprint.iacr.org/2020/852.pdf) protocol. FROST stands for Flexible Round-Optimized Schnorr Threshold Signatures, a protocol that surpasses other threshold signature protocols with its efficient single-round signing procedure. PyFrost utilizes the standard FROST protocol for single-round signing operations. Additionally, it incorporates the [Identifiable Cheating Entity FROST Signature Protocol](https://eprint.iacr.org/2021/1658.pdf) within the *distributed key generation (DKG)* framework. This approach is designed to detect and mitigate potential malicious behavior, such as when cheating entities selectively share secrets during the DKG process to exclude honest participants.

[This tutorial](https://github.com/SAYaghoubnejad/pyfrost/wiki/PyFrost-TSS-Protocl) provides an introduction to cryptographic concepts integral to PyFrost, including Threshold Signatures, Distributed Key Generation, Cheating Identification, Standard Schnorr Signatures, and Single-Round Schnorr Threshold Signatures.

PyFrost implements the cryptographic functions of the FROST protocol and includes a networking package that features libp2p clients for nodes, signature aggregators, and distributed key generators.


## Cryptography Classes & Functions

```python
pyfrost.KeyGen(self, dkg_id, threshold, n, node_id, partners, coefficient0=None)
```
- **Description:** This class is responsible for generating a distributed key based on the FROST algorithm. After key generation, `KeyGen.dkg_key_pair` should be saved, and this object can be deleted.
- **Inputs:**
  - `dkg_id` **str**: The ID corresponding to the key that will be generated.
  - `threshold` **int**: The threshold of the key (i.e., $t$).
  - `n` **int**: The total number of nodes contributing to the generation of this key.
  - `node_id` **str**: The ID of the current node.
  - `partners` **List[str]**: The list of all nodes' IDs contributing to the generation of this key.
  - `coefficient0` **int**, **default=None**: The coefficient of $x^0$ (i.e., $a_0$) of the polynomial generated in `round1()`.
- **Example:**
  ```python
  >>> key_gen = KeyGen(dkg_id, threshold, n, node_id, partners)
  ```

- **Functions:**
  ```python
  pyfrost.KeyGen.round1(self)
  ```
  - **Description:** Initiates the *distributed key generation (DKG)* by generating a key pair (used for securing communication in subsequent rounds against eavesdropping) and a $t$-degree polynomial for the distributed key. Then, it returns the data that needs to be broadcast to other nodes in the network for the following round of DKG.
  - **Inputs:** `None`
  - **Outputs:** 
    - Returns the data (as a dictionary) that needs to be broadcast to all nodes in the party.
  - **Example:**
    ```python
    >>> key_gen.round1()
    {'sender_id': '1', 'public_fx': [354869359782458571095890413565465978453788179974689225985932959388312230579979, 247500362764762459947037982734794064054965566413621565599364790220368476413502], 'coefficient0_signature': {'nonce': 383490719566463586209512810251721527549668124580471769569263292052718615717605, 'signature': '0xcbf8c729dad4e12ed897b4c8be96b7cb5a3eccd4392739eb4b51d039c97ecac77a0d772c7590695cbb2eb138df391ce5eb8e435623800e536cefe8c856805f8b'}, 'public_key': 324477578860614943258278830477072100212788902702977958207661649946147662330559, 'secret_signature': {'nonce': 426048566373482137317695608623139678632846866919427725330338763171376438819092, 'signature': '0x7953fa95c57833fc061b34859c2589ef06372f79fb2da18051b701b105c2684dcf410c15f86505968096b3e4d7ad805a96ca0d1657ae225f694b412a40059f45'}}
    ```

  ```python
  pyfrost.KeyGen.round2(self, round1_broadcasted_data)
  ```
  - **Description:** Processes the second round of DKG by handling `round1_broadcasted_data` from other party nodes. It generates data to be shared between node pairs, encrypting it with the sender's private key and the receiver's public key (generated at the beginning of `round1`).
  - **Inputs:**
    - `round1_broadcasted_data` **dict**: Data broadcasted in `round1` by all other party nodes.
  - **Outputs:** 
    - Returns the data (as a dictionary) to be sent to each node.
  - **Example:**
    ```python
    >>> key_gen.round2(broadcasted_data)
    [{'receiver_id': '2', 'sender_id': '1', 'data': 'gAAAAABlipVMSH1zoNxCAWyxWi1JYYH3BK_QR2ikKAmzUfxAyw2NR6baP-UROk2p6EirC6UajvGq-Lvq1d2_WrOoNU0y6G6vlofV_fdYsXLZyxOjpm-l3KtmGrslCRN5sj8X_egMf9hBBA3scTLYRxSC5P3yLrAS4hB4KqWj2N64PsIm_BQmJtH9q-3iX7oYkRPEDSY7Sx6tCJn7Xio3NI17yDzQOpt4Xw=='}]
    ```

  ```python
  pyfrost.KeyGen.round3(self, round2_encrypted_data)
  ```
  - **Description:** Calculates the node's share of the distributed key, reporting the share and corresponding key, signed with the node's permanent secret for verification (to set the new key on contract). In case of failure due to other nodes' dishonesty, it reports malicious activity.
  - **Inputs:**
    - `round2_encrypted_data` **dict**: Data received in `round2` where this node is the receiver.
  - **Outputs:** 
    - Returns a dictionary containing `status` and `data`. If `status` is `SUCCESSFUL`, `data` includes the distributed key, the node's share of this key, and a signature. If `status` is `COMPLAINT`, it contains evidence of another node's dishonesty.
  - **Example:**
    ```python
    >>> key_gen.round3(secret_data)
    {'share': 258184534306628725651417970045960225810129798775481439243461248905229424821005, 'dkg_public_key': 330020007264580023461702987042999164784659928898693899624672734148152731831723}
    ```

```python
pyfrost.Key(self, dkg_key, node_id)
```
- **Description:** This class represents the FROST key that can be used for signing.
- **Inputs:**
  - `dkg_key` **Dict**: A dictionary containing the share of the key owned by this node and the corresponding distributed public key.
  - `node_id` **str**: The ID of the current node.
- **Example:**
  ```python
  >>> key = Key(key_pair, self.peer_id)
  ```

- **Functions:**
  ```python
  pyfrost.Key.sign(self, commitments_dict, message, nonces)
  ```
  - **Description:** This function generates a part of the signature using the respective share of the distributed key it owns.  
  - **Inputs:**
    - `commitments_dict` **Dict**: A dictionary containing nonces from all nodes contributing to signature generation (which should be ≥ $t$

).
    - `message` **str**: The message to be signed.
    - `nonces` **Dict**: A dictionary containing all the nonces that this node has generated.
  - **Outputs:** 
    - Returns a pair of `(signature, used_nonce)`. `signature` is a dictionary containing the part of the signature that this node is responsible for generating. `used_nonce` indicates the nonce that was used in this signature and should be deleted.
  - **Example:**
    ```python
    >>> key.sign(commitments_list, result['hash'], nonces)
    ({'id': 1, 'signature': 4380775917818667649812480154896800544056187746415147033529676022466003781424, 'public_key': 242384563336956347086629547533773811569873617465034862979014339799278646286561, 'aggregated_public_nonce': 405219060927290873028863696293410269081074583578299458274783889090092789052128}, {'nonce_d_pair': {370874977114582033781122528087428995876126991915439375306690750715323470958581: 2213281037472537998716995430904520710481785332851970727722116598008453328508}, 'nonce_e_pair': {378212709838154422461267498938698569339673057809356891364745026324345749064958: 89196692178909244182952791960826909494694018849626789515424045125548267120866}})
    ```

```python
pyfrost.create_nonces(node_id, number_of_nonces)
```
- **Description:** This function generates a batch of nonces used when issuing signatures.  
- **Inputs:**
  - `node_id` **int**: The ID of the current node.
  - `number_of_nonces` **int**, **default=10**: The number of nonces requested to be generated.
- **Outputs:** 
  - Returns a pair of `(nonce_publics, nonce_privates)`. `nonce_publics` is a dictionary containing the public part of the nonce that should be sent to the Signature Aggregator (`SA`). `nonce_privates` indicates the private part of the nonce that should be stored in the `Node`.
- **Example:**
  ```python
  >>> pyfrost.create_nonces(int(node_id), number_of_nonces)
  [{'id': 1, 'public_nonce_d': 305959749411128529065578653080012926400260502965593237683903546682436926831957, 'public_nonce_e': 305142297584683785301649306463683229438777535204575943484807365866294802306735}, {'id': 1, 'public_nonce_d': 437808753910339401580275647953401913867793902236558518392480162633846420791540, 'public_nonce_e': 414707015006718467080421944719135610819227765812054941443016883164601097199535}]
  ```

```python
pyfrost.aggregate_nonce(message, commitments_dict, group_key)
```
- **Description:** This function is used to aggregate nonces and calculate an aggregated nonce used for verifying the aggregated signature.
- **Inputs:**
  - `message` **str**: The message that was signed.
  - `commitments_dict` **Dict**: A dictionary containing nonces from all nodes contributing to the signature to be aggregated.
  - `group_key` **Point**: A point indicating the distributed key generated using `KeyGen`.
- **Outputs:** 
  - Returns a **Point** indicating the aggregated nonce.
- **Example:**
  ```python
  >>> pyfrost.aggregate_nonce(str_message, commitments_dict, dkg_key['public_key'])
  X: 0xc5ae5888e8866bc57531d26ff22a3b8534a2b74ca82fdf445c8dfb50540eb4b1
  Y: 0x2e944f35abb9a3a9926518bd2bb95cd4092ae6058bdb052dcd857a5b36ed2dc0
  (On curve <secp256k1>)
  ```

```python
pyfrost.aggregate_signatures(message, single_signatures, aggregated_public_nonce, group_key)
```
- **Description:** This function is used to aggregate signatures and calculate an aggregated signature that is verifiable by anyone.
- **Inputs:**
  - `message` **str**: The message that was signed.
  - `single_signatures` **List[Dict[str, int]]**: A list containing shares of the signature that each node generates.
  - `aggregated_public_nonce` **Point**: The aggregated nonce.
  - `group_key` **int**: An integer indicating the distributed key generated using `KeyGen`.
- **Outputs:** 
  - Returns a dictionary containing all data needed to verify the aggregated signature (i.e., `nonce`, `public_key`, `aggregated_signature`, `message_hash`).
- **Example:**
  ```python
  >>> pyfrost.aggregate_signatures(str_message, signs, aggregated_public_nonce, dkg_key['public_key'])
  {'nonce': '0xc531f2Fff016aeDF48fdb51B199a74306391B13c', 'public_key': {'x': '0xd9a0b467f4f5e5f1a18ca25cb4bb47da95e6a86f2056ee1deeba8f41e7970dab', 'y_parity': 0}, 'signature': 97753292422535281194543953719677706936829466537191776216895420033273107515779, 'message_hash': HexBytes('0x260f59626b383fe31873d9bef3f6a5262af6206e8eb50088da9e41fb9e87dc41')}
  ```

```python
pyfrost.verify_group_signature(aggregated_signature)
```
- **Description:** This function verifies the aggregated signature.
- **Inputs:**
  - `aggregated_signature` **Dict**: A dictionary containing `nonce`, `public_key`, `aggregated_signature`, `message_hash`.
- **Outputs:** 
  - Returns a boolean indicating whether the signature is verified or not.
- **Example:**
  ```python
  >>> pyfrost.frost.verify_group_signature(aggregated_sign)
  True
  ```

```python
pyfrost.verify_single_signature(id, message, commitments, aggregated_nonce, public_key_share, signature, group_key)
```
- **Description:** This function verifies the share of the signature generated by each node.
- **Inputs:**
  - `id` **int**: The ID of the current node.
  - `message` **str**: The message that was signed.
  - `commitments` **Dict**: A dictionary containing nonces from all nodes contributing to signature generation.
  - `aggregated_nonce` **Point**: The aggregated nonce.
  - `public_key_share` **int**: The node's share of the distributed key (i.e., `group_key`).
  - `signature` **Dict**: The node's generated share of the signature.
  - `group_key` **Point**: A point indicating the distributed key generated using `KeyGen`.
- **Outputs:** 
  - Returns a boolean indicating whether the share of the signature is verified or not.
- **Example:**
  ```python
  >>> pyfrost.pyfrost.verify_single_signature(sign['

## Network Package

The network package includes the implementation of the following components:

#### Node
A Libp2p client that facilitates the three rounds of the Distributed Key Generation (DKG) process, as well as nonce creation and signing methods.

#### Distributed Key Generator
A Libp2p client responsible for initiating the DKG process through the node.

#### Signature Aggregator
A Libp2p client that collects nonces, requests signatures from nodes, and then aggregates and verifies them.

To effectively utilize PyFrost in your Threshold Signature Scheme (TSS) network, the following interface classes, used by the above clients, should be implemented:
- **Data Manager**: Functions for storing and retrieving private nonces and keys.
- **Node Info**: Provides a list of network nodes along with their information.
- **Validators**: Verifies the roles of signature aggregators and distributed key generators.

**Note:** Examples of how to implement these abstract interfaces can be found in `pyfrost/network/examples/abstracts.py`.

## How to Setup

```bash
$ git clone https://github.com/SAYaghoubnejad/pyfrost.git
$ cd pyfrost
$ virtualenv -p python3.10 venv
$ source venv/bin/activate
(venv) $ pip install .
```

**Note:** Python version `3.10` is required.

## How to Run an Example

To run an example network, open `m` additional terminals for `m` nodes and activate the `venv` in these terminals. Note that `m` is an arbitrary positive number, but it must not exceed 99 due to predefined nodes in the example setup. Then navigate to the `pyfrost/network/examples/` directory:

```bash
(venv) $ cd pyfrost/network/examples/
```

First, initialize the nodes by typing the following command in `m` terminals:

```bash
(venv) $ python node.py [0-m]
```

Wait for the node setup to complete, which is indicated by the node API being printed and a message stating **Waiting for incoming connections...**

Finally, run the `example.py` script in the last terminal:

```bash
(venv) $ python example.py [number of nodes you ran] [threshold] [n] [number of signatures]
```

The `example.py` script manages distributed key generation and signature aggregation.

The script requires 4 parameters:

1. `number of nodes you ran`: The count of active nodes.
2. `threshold`: The FROST algorithm threshold, an integer ($t \leq n$).
3. `n`: The number of nodes collaborating in the DKG to generate a distributed key ($n \leq m$).
4. `number of signatures`: The count of signatures requested by the signature aggregator after the DKG.

**Note:** Logs for each node and the signature aggregator are stored in the `./logs` directory.

## Benchmarking

The following benchmarks were conducted on an Intel i7-6700HQ with 8 cores and 16GB RAM. (All times are in seconds)

| Benchmark                     | DKG Time | Avg. Time per Node for Nonce Generation | Signing Time |
|-------------------------------|----------|----------------------------------------|--------------|
|  7 of 10                      | 0.840 sec| 0.352 sec                              | 0.135 sec    | 
| 15 of 20                      | 5.435 sec| 0.344 sec                              | 0.380 sec    |
| 25 of 30                      |14.183 sec| 0.345 sec                              | 0.601 sec    |

For the non-local evaluation, we utilized 30 node containers spread across three countries and four cities. Additionally, the Signature Aggregator was configured with dual vCPUs and 8GB of RAM.

| Benchmark                     | DKG Time | Avg. Time per Node for Nonce Generation | Signing Time |
|-------------------------------|----------|----------------------------------------|--------------|
| 25 of 30                      | 7.400 sec| 1.594 sec                              | 0.725 sec    |