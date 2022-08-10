import hashlib
import pickle


def _get_hash(args, protocol):
    picklestring = _serialize(args, protocol)
    return hashlib.sha224(picklestring).hexdigest()


def _serialize(args, protocol):
    return pickle.dumps(args, protocol=protocol)