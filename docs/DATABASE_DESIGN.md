erDiagram
    USERS {
        int id PK
        string firebase_uid UK
        string full_name
        string email UK
        string role
        boolean is_active
        datetime last_login_at
        datetime created_at
        datetime updated_at
    }

    RESTAURANT_SETTINGS {
        int id PK
        string restaurant_name
        string address
        string phone
        string email
        string gstin
        decimal default_gst_percentage
        string currency
        string invoice_prefix
        string receipt_footer
        string logo_path
        string timezone
        datetime created_at
        datetime updated_at
    }

    DINING_TABLES {
        int id PK
        string table_number UK
        int capacity
        string area
        string description
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    CUSTOMERS {
        int id PK
        int user_id FK
        string full_name
        string phone
        string email
        string address
        string notes
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    RESERVATIONS {
        int id PK
        string reservation_number UK
        int customer_id FK
        int table_id FK
        int created_by_user_id FK
        datetime start_time
        datetime end_time
        int guest_count
        string status
        string notes
        string cancellation_reason
        datetime cancelled_at
        datetime created_at
        datetime updated_at
    }

    MENU_CATEGORIES {
        int id PK
        string name UK
        string description
        int display_order
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    MENU_ITEMS {
        int id PK
        int category_id FK
        string name
        string description
        decimal price
        string food_type
        string image_path
        boolean is_available
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    ORDERS {
        int id PK
        string order_number UK
        int customer_id FK
        int table_id FK
        int reservation_id FK
        int created_by_user_id FK
        string order_type
        string status
        string special_instructions
        string delivery_address
        datetime completed_at
        datetime cancelled_at
        string cancellation_reason
        datetime created_at
        datetime updated_at
    }

    ORDER_ITEMS {
        int id PK
        int order_id FK
        int menu_item_id FK
        string item_name
        decimal unit_price
        int quantity
        string special_instruction
        decimal line_total
        datetime created_at
    }

    INVOICES {
        int id PK
        int order_id FK
        string invoice_number UK
        decimal subtotal
        string discount_type
        decimal discount_value
        decimal discount_amount
        decimal gst_percentage
        decimal gst_amount
        decimal grand_total
        string payment_method
        string payment_status
        datetime paid_at
        datetime refunded_at
        string refund_reason
        datetime created_at
        datetime updated_at
    }

    USERS o|--o| CUSTOMERS : "customer account"
    USERS ||--o{ RESERVATIONS : creates
    USERS ||--o{ ORDERS : creates

    CUSTOMERS ||--o{ RESERVATIONS : makes
    CUSTOMERS o|--o{ ORDERS : places

    DINING_TABLES ||--o{ RESERVATIONS : receives
    DINING_TABLES o|--o{ ORDERS : serves

    RESERVATIONS o|--o| ORDERS : becomes

    MENU_CATEGORIES ||--o{ MENU_ITEMS : contains
    MENU_ITEMS ||--o{ ORDER_ITEMS : referenced_by

    ORDERS ||--|{ ORDER_ITEMS : contains
    ORDERS ||--o| INVOICES : billed_by