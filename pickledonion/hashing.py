import hashlib
import pickle


def _get_hash(args):
    picklestring = _serialize(args)
    return hashlib.sha224(picklestring).hexdigest()


def _serialize(args):
    return pickle.dumps(args, protocol=3)