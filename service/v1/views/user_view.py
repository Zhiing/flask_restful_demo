"""
@Time    : 18-4-23 下午2:36
@Author  : xionzhi
@Desc    : 用户
"""

from service import db, logger

from flask import request
from sqlalchemy import func, and_, or_
from flask_restful import Resource
from flask_bcrypt import check_password_hash

from service.v1.permissions import verify_token
from service.common import (AccountRepeatException,
                            RequestParameterException,
                            AccountPasswdErrorException,
                            AccountPasswdShortException)

from service.models import (DIDUserModel,
                            DIDGroupModel)

from service.models import (DICUserStatusModel,
                            DICGroupTypeModel,
                            DICGroupStatusModel)

from service.v1.serializers import (DIDUserSchema,
                                    DIDGroupSchema,
                                    DICUserStatusSchema,
                                    DICGroupTypeSchema,
                                    DICGroupStatusSchema)


class UserView(Resource):
    @verify_token(request)
    def get(self):
        _login_user_info = getattr(request, 'login_user_info')

        try:
            user_query = db.session.query(DIDUserModel.id,
                                          DIDUserModel.passwd,
                                          DIDUserModel.phone,
                                          DIDUserModel.email,
                                          DIDUserModel.photo,
                                          DIDUserModel.group_id,
                                          DIDUserModel.status,
                                          DIDUserModel.ctime,
                                          DIDUserModel.mtime). \
                filter(DIDUserModel.status != 0,
                       DIDUserModel.id == _login_user_info.get('id')).first()

            resp_data = DIDUserSchema().dump(user_query).data

            return {'code': 200, 'resp_data': resp_data}
        except Exception as e:
            db.session.rollback()
            logger.error(e)
            raise e

    @verify_token(request)
    def post(self):
        _username = request.json.get('userName')
        _passwd = request.json.get('passWord')
        _phone = request.json.get('phoneNumber')
        _email = request.json.get('userEmail')
        _group_id = request.json.get('groupId')

        try:
            if None in (_username, _passwd, _phone, _email, _group_id):
                raise RequestParameterException

            user_query = db.session.query(DIDUserModel.id,
                                          DIDUserModel.phone,
                                          DIDUserModel.email). \
                filter(or_(DIDUserModel.phone == _phone,
                           DIDUserModel.email == _email)).first()
            if user_query is not None:
                if user_query.phone == _phone:
                    raise AccountRepeatException
                elif user_query.email == _email:
                    raise AccountRepeatException

            _user_data = DIDUserModel(
                uname=_username,
                _password=_passwd,
                phone=_phone,
                email=_email,
                group_id=_group_id)
            db.session.add(_user_data)
            db.session.commit()

            resp_data = DIDUserSchema().dump(_user_data).data

            return {'code': 200, 'resp_data': resp_data, 'message': '添加成功'}
        except Exception as e:
            db.session.rollback()
            logger.error(e)
            raise e

    @verify_token(request)
    def patch(self):
        _login_user_info = getattr(request, 'login_user_info')
        _passwd = request.json.get('passWord')

        try:
            if len(_passwd) < 6:
                raise AccountPasswdShortException

            db.session.query(DIDUserModel). \
                filter(DIDUserModel.id == _login_user_info.get('id')). \
                update({DIDUserModel._password: _passwd})
            db.session.commit()

            return {'code': 200, 'message': '修改成功'}
        except Exception as e:
            db.session.rollback()
            logger.error(e)
            raise e

    @verify_token(request)
    def put(self):
        pass

    @verify_token(request)
    def delete(self):
        _login_user_info = getattr(request, 'login_user_info')
        _passwd = request.json.get('passWord')

        try:
            user_query = db.session.query(DIDUserModel.id,
                                          DIDUserModel.passwd,
                                          DIDUserModel.status). \
                filter(DIDUserModel.status != 0,
                       DIDUserModel.id == _login_user_info.get('id'))

            if check_password_hash(user_query.first().passwd, _passwd) is False:
                raise AccountPasswdErrorException

            user_query.update({DIDUserModel.status: 0})
            db.session.commit()

            return {'code': 200, 'message': '删除成功'}
        except Exception as e:
            db.session.rollback()
            logger.error(e)
            raise e
