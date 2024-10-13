# syntax = "proto3";

# message User {
#     string email = 1;     // User's email address
#     string name = 2;      // User's name
# }

# message Order {
#     string id = 1;                 // Order ID
#     string order_user_name = 2;    // User's name for the order
# }

# enum MessageType {
#     user_event = 0;   // Event related to user actions
#     order_event = 1;  // Event related to order actions
#     email_notification = 2; // Email notification event
#     sms_notification = 3;   // SMS notification event
# }

# message EmailNotification {
#     string subject = 1;        // Subject of the email
#     string body = 2;           // Body of the email
#     string recipient_email = 3; // Email address of the recipient
# }

# message SMSNotification {
#     string phone_number = 1;   // Phone number to send SMS
#     string message = 2;        // Message content for the SMS
# }

# message NotificationMessage {
#     MessageType message_type = 1; // Type of notification message
#     User user = 2;                 // User related to the event
#     Order order = 3;               // Order related to the event
#     EmailNotification email = 4;   // Email notification details
#     SMSNotification sms = 5;       // SMS notification details
# }
# // notification.proto
# syntax = "proto3";

# package notification;

# // آرڈر اپڈیٹ ایونٹ کے لیے میسج
# message OrderUpdate {
#     string order_id = 1;
#     string user_id = 2;
#     string order_status = 3;
# }

# // صارف کی معلومات کے لیے میسج
# message User {
#     string id = 1;
#     string email = 2;
# }

# // پروٹوکول بفرز میسج جو کاکا (Kafka) کے ذریعے بھیجا جائے گا
# message NotificationMessage {
#     oneof message_type {
#         OrderUpdate order_update = 1;
#         User user = 2;
#     }
# }
# syntax = "proto3";

# message UserNotification {
#     string email = 1;
#     string id = 2;
# }

# message OrderNotification {
#     string order_id = 1;
#     string status = 2;
#     string user_id = 3;
# }

# message NotificationMessage {
#     oneof notification_type {
#         UserNotification user_notification = 1;
#         OrderNotification order_notification = 2;
#     }
# }
