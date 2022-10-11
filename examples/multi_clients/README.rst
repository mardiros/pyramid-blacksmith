Example with multiple clients
=============================

This example is a dummy microservice stack that send email to a user.

This is a copy/paste of the consul_sd service, and we adapt it
to use a `RouterDiscovery` to get a Server-Side Discovery
architecture.


Call the service
----------------

::

   # Use static
   curl -H "Content-Type: application/json" \
      --data '{"username": "naruto", "message": "Datte Bayo"}' \
      -X POST http://router.localhost/notif-v1/v1/notification

   # Use consul
   curl -H "Content-Type: application/json" \
      --data '{"username": "naruto", "message": "Datte Bayo"}' \
      -X POST http://router.localhost/notif-v1/v2/notification

   # Use router
   curl -H "Content-Type: application/json" \
      --data '{"username": "naruto", "message": "Datte Bayo"}' \
      -X POST http://router.localhost/notif-v1/v3/notification


Check result
------------

The mailbox is available in a web application http://mailhog.localhost/
to view the email has been properly received.
