""" ACL parsing stuff """

from kazoo.security import (
    ACL,
    Id,
    make_acl,
    make_digest_acl,
    Permissions
)


class ACLReader:
    class BadACL(Exception): pass

    valid_schemes = [
        "world",
        "auth",
        "digest",
        "host",
        "ip",
        "username_password",  # internal-only: gen digest from user:password
    ]

    @classmethod
    def extract(cls, acls):
        return list(map(cls.extract_acl, acls))

    @classmethod
    def extract_acl(cls, acl):
        try:
            scheme, rest = acl.split(":", 1)
            credential = ":".join(rest.split(":")[0:-1])
            cdrwa = rest.split(":")[-1]
        except ValueError:
            raise cls.BadACL("Bad ACL: %s. Format is scheme:id:perms" % (acl))

        if scheme not in cls.valid_schemes:
            raise cls.BadACL("Invalid scheme: %s" % (acl))

        create = True if "c" in cdrwa else False
        read = True if "r" in cdrwa else False
        write = True if "w" in cdrwa else False
        delete = True if "d" in cdrwa else False
        admin = True if "a" in cdrwa else False

        if scheme == "username_password":
            try:
                username, password = credential.split(":", 1)
            except ValueError:
                raise cls.BadACL("Bad ACL: %s. Format is scheme:id:perms" % (acl))
            return make_digest_acl(username,
                                   password,
                                   read,
                                   write,
                                   create,
                                   delete,
                                   admin)
        else:
            return make_acl(scheme,
                            credential,
                            read,
                            write,
                            create,
                            delete,
                            admin)

    @classmethod
    def to_dict(cls, acl):
        return {
            "perms": acl.perms,
            "id": {
                "scheme": acl.id.scheme,
                "id": acl.id.id
            }
        }

    @classmethod
    def from_dict(cls, a):
        perms = a.get("perms", Permissions.ALL)
        id_dict = a.get("id", {})
        id_scheme = id_dict.get("scheme", "world")
        id_id = id_dict.get("id", "anyone")
        return ACL(perms, Id(id_scheme, id_id))
