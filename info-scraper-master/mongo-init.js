db.createUser(
    {
        user: "root",
        pwd: "lala2020",
        roles: [
            {
                role: "userAdminAnyDatabase",
                db: "admin"
            }
        ]
    }
);