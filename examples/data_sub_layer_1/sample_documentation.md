# API Documentation

## Overview
This document describes the REST API endpoints for our e-commerce platform.

## Authentication
All API requests require authentication using Bearer tokens.

```
Authorization: Bearer <your-token>
```

## Base URL
```
https://api.example.com/v1
```

## Endpoints

### Products

#### GET /products
Retrieve all products with optional filtering.

**Parameters:**
- `category` (optional): Filter by product category
- `in_stock` (optional): Filter by stock availability (true/false)
- `limit` (optional): Maximum number of results (default: 50)

**Response:**
```json
{
  "products": [
    {
      "product_id": "P001",
      "name": "Wireless Headphones",
      "price": 99.99,
      "category": "Electronics"
    }
  ],
  "total": 1,
  "page": 1
}
```

#### POST /products
Create a new product.

**Request Body:**
```json
{
  "name": "Product Name",
  "category": "Electronics",
  "price": 99.99,
  "specifications": {}
}
```

### Orders

#### GET /orders
Retrieve orders for the authenticated user.

**Parameters:**
- `status` (optional): Filter by order status
- `date_from` (optional): Start date filter (YYYY-MM-DD)
- `date_to` (optional): End date filter (YYYY-MM-DD)

#### POST /orders
Create a new order.

**Request Body:**
```json
{
  "customer_id": 1,
  "product_ids": ["P001", "P002"],
  "shipping_address": {
    "street": "123 Main St",
    "city": "New York",
    "zip": "10001"
  }
}
```

## Error Handling

The API uses standard HTTP status codes:

- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error

Error responses include a message:
```json
{
  "error": "Product not found",
  "code": "PRODUCT_NOT_FOUND"
}
```

## Rate Limiting

API requests are limited to 1000 requests per hour per API key.

## Support

For API support, contact: api-support@example.com