# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: payment.proto
# Protobuf Python Version: 5.28.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    28,
    1,
    '',
    'payment.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rpayment.proto\"\xba\x01\n\x07Payment\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x10\n\x08order_id\x18\x02 \x01(\x05\x12\x0f\n\x07user_id\x18\x03 \x01(\x05\x12\x0e\n\x06\x61mount\x18\x04 \x01(\x02\x12\x10\n\x08\x63urrency\x18\x05 \x01(\t\x12\x16\n\x0epayment_method\x18\x06 \x01(\t\x12\x1e\n\x06status\x18\x07 \x01(\x0e\x32\x0e.PaymentStatus\x12\x12\n\ncreated_at\x18\x08 \x01(\t\x12\x12\n\nupdated_at\x18\t \x01(\t\"h\n\x0ePaymentMessage\x12\"\n\x0cmessage_type\x18\x01 \x01(\x0e\x32\x0c.MessageType\x12\x1e\n\x0cpayment_data\x18\x02 \x01(\x0b\x32\x08.Payment\x12\x12\n\npayment_id\x18\x03 \x01(\x05*P\n\x0bMessageType\x12\x12\n\x0e\x43REATE_PAYMENT\x10\x00\x12\x12\n\x0eUPDATE_PAYMENT\x10\x01\x12\x19\n\x15PAYMENT_STATUS_UPDATE\x10\x03*E\n\rPaymentStatus\x12\x0b\n\x07PENDING\x10\x00\x12\r\n\tCOMPLETED\x10\x01\x12\n\n\x06\x46\x41ILED\x10\x02\x12\x0c\n\x08REFUNDED\x10\x03\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'payment_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_MESSAGETYPE']._serialized_start=312
  _globals['_MESSAGETYPE']._serialized_end=392
  _globals['_PAYMENTSTATUS']._serialized_start=394
  _globals['_PAYMENTSTATUS']._serialized_end=463
  _globals['_PAYMENT']._serialized_start=18
  _globals['_PAYMENT']._serialized_end=204
  _globals['_PAYMENTMESSAGE']._serialized_start=206
  _globals['_PAYMENTMESSAGE']._serialized_end=310
# @@protoc_insertion_point(module_scope)
