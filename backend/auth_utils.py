#General library imports
from typing import List
import json
import base64
from copy import copy
import os


#Import FastAPI dependencies
from fastapi import Depends, HTTPException
from fastapi_sqlalchemy import db
from fastapi.security import OAuth2PasswordBearer

#Import SQLAlchemy dependencies

#Import libraries for token decryption
from jose import jwt, jws
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

#Import schemas from schemas.py
from schemas import HoursUserBase as SchemaHoursUserBase

#Import models from models.py
from models import HoursUser as ModelHoursUser

from database import SessionLocal
from dotenv import load_dotenv

load_dotenv(".env")
DISCOVERY_URL = os.getenv("DISCOVERY_URL")

#OAuthScheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "token")

def _b64_decode(data):
    data += '=' * (4 - len(data) % 4)
    return base64.b64decode(data).decode('utf-8')

def jwt_header_decode(jwt):
    header, _, _ = jwt.split('.')
    return json.loads(_b64_decode(header))


def jwt_payload_decode(jwt):
    _, payload, _ = jwt.split('.')
    return json.loads(_b64_decode(payload))

async def get_user (token: str = Depends(oauth2_scheme)):
    try:
        decoded_token = jwt_payload_decode(token)
        username = decoded_token['name']
        email = decoded_token['unique_name']
    
        user=db.session.query(ModelHoursUser).filter(ModelHoursUser.username  == username,
                                                     ModelHoursUser.email  == email).first()

        return SchemaHoursUserBase(username=user.username,
                               email = user.email,
                               role=user.role)
    except Exception as e :
        raise HTTPException(status_code=401, detail="User not found")



# Authentication Middleware
async def test_auth (token: str = Depends(oauth2_scheme)):
    response=requests.get(DISCOVERY_URL)
    data = response.json()
    public_keys_uri = data
    public_keys = requests.get(public_keys_uri["jwks_uri"]).json()

    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    alg = header.get("alg")

    key = next(key for key in public_keys["keys"] if key["kid"] == kid)
    modulus = base64.urlsafe_b64decode(key["n"] + "==")
    exponent_bytes = base64.urlsafe_b64decode(key["e"] + "==")
    exponent = int.from_bytes(exponent_bytes, byteorder="big", signed=False)
    mod = int.from_bytes(modulus, byteorder="big", signed=False)

    # Construct RSA public key
    public_numbers = rsa.RSAPublicNumbers(exponent, mod)
    public_key = public_numbers.public_key()

    # Serialize the RSA public key to PEM format
    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Convert bytes to string and remove leading/trailing whitespaces
    pem_public_key_str = pem_public_key.decode("utf-8").strip()
    
    verif = jws.verify(token,pem_public_key,alg)

    return pem_public_key_str

# Fetch the Azure public key
def get_azure_public_key():
    response=requests.get(DISCOVERY_URL)
    if response.status_code == 200:
         data = response.json()
         print(data)
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch public keys")
