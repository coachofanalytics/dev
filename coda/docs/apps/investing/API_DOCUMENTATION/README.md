# CODA Investing App - API Documentation

## 🎯 **Overview**

The CODA Investing App provides comprehensive RESTful API endpoints for investment management, risk assessment, portfolio tracking, and analytics. All APIs follow REST principles and return JSON responses.

---

## 🔐 **Authentication & Security**

### **Authentication Methods**
- **Session Authentication**: Django session-based authentication
- **CSRF Protection**: All POST/PUT/DELETE requests require CSRF tokens
- **Login Required**: All endpoints require user authentication

### **CSRF Token Handling**
```javascript
// Include CSRF token in AJAX requests
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            xhr.setRequestHeader("X-CSRFToken", $('[name=csrfmiddlewaretoken]').val());
        }
    }
});
```

---

## 📊 **Investment Management APIs**

### **Investment Dashboard**
```http
GET /investing/dashboard/
```
**Response:**
```json
{
    "investments": [
        {
            "id": 1,
            "investment_type": "equity",
            "amount_invested": "10000.00",
            "current_value": "10500.00",
            "actual_return_rate": "5.00",
            "status": "active",
            "investment_date": "2025-01-15"
        }
    ],
    "total_invested": "50000.00",
    "total_current_value": "52500.00",
    "total_returns_paid": "2500.00",
    "overall_return_percentage": "5.00"
}
```

### **Investment List**
```http
GET /investing/individual-investments/
```
**Query Parameters:**
- `page`: Page number (default: 1)
- `status`: Filter by status (active, completed, pending)
- `investment_type`: Filter by investment type

**Response:**
```json
{
    "count": 25,
    "next": "http://example.com/investing/individual-investments/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "investment_type": "equity",
            "amount_invested": "10000.00",
            "current_value": "10500.00",
            "actual_return_rate": "5.00",
            "status": "active",
            "investment_date": "2025-01-15",
            "url": "/investing/individual-investment/1/"
        }
    ]
}
```

### **Create Investment**
```http
POST /investing/create-individual-investment/
```
**Request Body:**
```json
{
    "investment_type": "equity",
    "amount_invested": "10000.00",
    "duration": 12,
    "investment_purpose": "Long-term growth investment",
    "model_type": "Installment",
    "expected_return_rate": "8.00",
    "risk_tolerance": "moderate"
}
```

**Response:**
```json
{
    "success": true,
    "investment_id": 123,
    "message": "Investment created successfully"
}
```

### **Update Investment Performance**
```http
POST /investing/update-performance/123/
```
**Request Body:**
```json
{
    "current_value": "11000.00",
    "actual_return_rate": "10.00",
    "total_returns_paid": "1000.00",
    "performance_notes": "Strong quarterly performance"
}
```

---

## 🎯 **Risk Management APIs**

### **Risk Dashboard**
```http
GET /investing/risk/risk-dashboard/
```
**Response:**
```json
{
    "risk_summary": {
        "total_investments": 25,
        "high_risk_investments": 3,
        "medium_risk_investments": 12,
        "low_risk_investments": 10,
        "active_alerts": 2,
        "compliance_issues": 1
    },
    "recent_assessments": [
        {
            "id": 1,
            "investment_id": 123,
            "assessment_date": "2025-10-25",
            "overall_risk_rating": "medium",
            "average_risk_score": 5.5
        }
    ],
    "active_alerts": [
        {
            "id": 1,
            "alert_type": "price_drop",
            "severity": "high",
            "message": "Investment value dropped 12% in 24 hours",
            "created_at": "2025-10-25T10:30:00Z"
        }
    ]
}
```

### **Create Risk Assessment**
```http
POST /investing/risk/risk-assessment/create/
```
**Request Body:**
```json
{
    "investment_id": 123,
    "market_risk_score": 6,
    "credit_risk_score": 4,
    "liquidity_risk_score": 5,
    "operational_risk_score": 3,
    "notes": "Quarterly risk assessment"
}
```

### **Risk Analytics**
```http
GET /investing/risk/api/risk-analytics/
```
**Response:**
```json
{
    "total_investments": 25,
    "risk_distribution": {
        "low": 10,
        "medium": 12,
        "high": 3
    },
    "active_alerts": 2,
    "average_risk_score": 4.8,
    "risk_trend": [
        {
            "date": "2025-10-01",
            "average_risk": 4.5
        },
        {
            "date": "2025-10-15",
            "average_risk": 4.7
        },
        {
            "date": "2025-10-25",
            "average_risk": 4.8
        }
    ]
}
```

### **Automated Risk Assessment**
```http
POST /investing/risk/auto-risk-assessment/123/
```
**Response:**
```json
{
    "success": true,
    "assessment_id": 456,
    "risk_rating": "medium",
    "average_risk_score": 5.5,
    "mitigation_strategies": [
        "Implement hedging strategies",
        "Increase monitoring frequency"
    ]
}
```

---

## 📈 **Portfolio Management APIs**

### **Portfolio List**
```http
GET /investing/myportfolio/
```
**Response:**
```json
{
    "count": 15,
    "results": [
        {
            "id": 1,
            "symbol": "AAPL",
            "industry": "Technology",
            "strategy": "covered_calls",
            "returns": "250.00",
            "amount": "5000.00",
            "created_at": "2025-10-20T14:30:00Z"
        }
    ]
}
```

### **Create Portfolio Entry**
```http
POST /investing/myportfoliocreate/
```
**Request Body:**
```json
{
    "symbol": "AAPL",
    "industry": "Technology",
    "strategy": "covered_calls",
    "amount": "5000.00",
    "long_strike": "150.00",
    "short_strike": "155.00",
    "number_of_contract": 10
}
```

### **Update Portfolio Entry**
```http
POST /investing/myportfolioupdate/AAPL/
```
**Request Body:**
```json
{
    "returns": "300.00",
    "comment": "Updated returns after option expiry"
}
```

---

## 📊 **Analytics APIs**

### **Investment Analytics**
```http
GET /investing/api/analytics/
```
**Query Parameters:**
- `investment_id`: Specific investment ID
- `date_from`: Start date (YYYY-MM-DD)
- `date_to`: End date (YYYY-MM-DD)
- `metric`: Analytics metric (performance, risk, returns)

**Response:**
```json
{
    "performance_metrics": {
        "total_return": "12.5",
        "annualized_return": "15.2",
        "sharpe_ratio": "1.8",
        "max_drawdown": "-8.3",
        "volatility": "12.1"
    },
    "risk_metrics": {
        "beta": "1.2",
        "alpha": "2.3",
        "treynor_ratio": "12.7",
        "information_ratio": "0.8"
    },
    "portfolio_metrics": {
        "total_value": "125000.00",
        "total_cost": "100000.00",
        "unrealized_gains": "25000.00",
        "realized_gains": "5000.00"
    }
}
```

### **Performance Data**
```http
GET /investing/api/performance/
```
**Response:**
```json
{
    "periods": [
        {
            "period": "2025-Q3",
            "start_value": "100000.00",
            "end_value": "105000.00",
            "return_amount": "5000.00",
            "return_percentage": "5.00"
        }
    ],
    "total_performance": {
        "total_return": "12.5",
        "annualized_return": "15.2"
    }
}
```

---

## 🎯 **Investment Plans APIs**

### **Investment Plans List**
```http
GET /investing/investment-plans/
```
**Response:**
```json
{
    "count": 8,
    "results": [
        {
            "id": 1,
            "name": "Tier 1 Growth Plan",
            "type": "investment",
            "tier": "Tier 1 ($1,000-$5,000)",
            "base_amount": 1000,
            "duration": 12,
            "rate": "8.00",
            "description": "Entry-level growth investment plan"
        }
    ]
}
```

### **Investment Plan Detail**
```http
GET /investing/investment-plans/1/
```
**Response:**
```json
{
    "id": 1,
    "name": "Tier 1 Growth Plan",
    "type": "investment",
    "tier": "Tier 1 ($1,000-$5,000)",
    "base_amount": 1000,
    "duration": 12,
    "rate": "8.00",
    "equity_ownership": "2.50",
    "platform_fee": "10.00",
    "tax": "5.00",
    "advantages": "Low minimum investment, competitive returns",
    "is_active": true,
    "is_featured": true
}
```

---

## 🔍 **Search & Filter APIs**

### **Investment Search**
```http
GET /investing/investments/?search=equity&status=active
```
**Query Parameters:**
- `search`: Search term
- `status`: Filter by status
- `investment_type`: Filter by type
- `date_from`: Start date filter
- `date_to`: End date filter
- `amount_min`: Minimum amount filter
- `amount_max`: Maximum amount filter

### **Portfolio Filter**
```http
GET /investing/myportfolio/?symbol=AAPL&strategy=covered_calls
```
**Query Parameters:**
- `symbol`: Stock symbol filter
- `strategy`: Trading strategy filter
- `industry`: Industry filter
- `date_from`: Start date filter
- `date_to`: End date filter

---

## 📋 **Error Handling**

### **Error Response Format**
```json
{
    "error": true,
    "error_code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
        "amount_invested": ["This field is required"],
        "investment_type": ["Invalid choice"]
    }
}
```

### **Common Error Codes**
- `VALIDATION_ERROR`: Form validation failed
- `PERMISSION_DENIED`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `INVALID_INVESTMENT`: Invalid investment data
- `RISK_THRESHOLD_EXCEEDED`: Risk threshold exceeded
- `COMPLIANCE_ISSUE`: Compliance requirement not met

### **HTTP Status Codes**
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## 🔧 **API Usage Examples**

### **JavaScript/AJAX Examples**

#### **Create Investment**
```javascript
$.ajax({
    url: '/investing/create-individual-investment/',
    method: 'POST',
    headers: {
        'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),
        'Content-Type': 'application/json'
    },
    data: JSON.stringify({
        investment_type: 'equity',
        amount_invested: '10000.00',
        duration: 12,
        investment_purpose: 'Long-term growth'
    }),
    success: function(response) {
        console.log('Investment created:', response);
        // Redirect or update UI
    },
    error: function(xhr, status, error) {
        console.error('Error:', xhr.responseJSON);
        // Handle error
    }
});
```

#### **Update Dashboard**
```javascript
function updateDashboard() {
    fetch('/investing/dashboard/')
        .then(response => response.json())
        .then(data => {
            // Update dashboard elements
            $('#total-invested').text('$' + data.total_invested);
            $('#current-value').text('$' + data.total_current_value);
            $('#total-returns').text('$' + data.total_returns_paid);
            $('#return-percentage').text(data.overall_return_percentage + '%');
        })
        .catch(error => console.error('Error:', error));
}

// Update every 30 seconds
setInterval(updateDashboard, 30000);
```

#### **Risk Assessment**
```javascript
function createRiskAssessment(investmentId, riskData) {
    fetch('/investing/risk/risk-assessment/create/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            investment_id: investmentId,
            ...riskData
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Risk assessment created successfully');
            location.reload();
        }
    })
    .catch(error => console.error('Error:', error));
}
```

---

## 📊 **Rate Limiting**

### **Rate Limits**
- **Standard Endpoints**: 100 requests per minute per user
- **Analytics Endpoints**: 20 requests per minute per user
- **Risk Assessment**: 10 requests per minute per user
- **Portfolio Updates**: 50 requests per minute per user

### **Rate Limit Headers**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## 🔒 **Security Best Practices**

### **API Security**
1. **Always use HTTPS**: All API calls must use HTTPS
2. **Validate Input**: Validate all input data
3. **CSRF Protection**: Include CSRF tokens in requests
4. **Rate Limiting**: Respect rate limits
5. **Error Handling**: Don't expose sensitive information in errors

### **Data Privacy**
1. **Minimal Data**: Only request necessary data
2. **Secure Storage**: Don't store sensitive data in localStorage
3. **Session Management**: Proper session handling
4. **Logout**: Clear sensitive data on logout

---

## 🚀 **API Versioning**

### **Current Version**
- **Version**: v1.0
- **Base URL**: `/investing/`
- **Format**: JSON

### **Future Versions**
- **v2.0**: Planned for Q2 2026
- **Features**: GraphQL support, real-time subscriptions
- **Migration**: Backward compatibility maintained

---

**Last Updated**: October 25, 2025  
**Version**: 1.0  
**Status**: ✅ Production Ready
