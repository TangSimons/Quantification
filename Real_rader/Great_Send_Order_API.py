import MetaTrader5 as mt5


# 市价开多单
def create_long_order(symbol, lot_size=0.1):
    price = mt5.symbol_info_tick(symbol).ask
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "comment": "开多单",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,  # 改为IOC更灵活
        "deviation": 20,  # 添加允许的滑点
    }
    result = mt5.order_send(request)
    order_id = result.order
    order_price = result.price
    return result, order_id, order_price


# 市价平多单
def stop_long_order(symbol, order_id, lot_size=0.1):
    price = mt5.symbol_info_tick(symbol).bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": mt5.ORDER_TYPE_SELL,
        "price": price,
        "position": order_id,  # 使用传入的order_id
        "comment": "平多单",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "deviation": 20,
    }
    result = mt5.order_send(request)
    order_price = result.price
    return result, order_price


# 市价开空单
def create_short_order(symbol, lot_size=0.1):
    price = mt5.symbol_info_tick(symbol).bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": mt5.ORDER_TYPE_SELL,
        "price": price,
        "comment": "开空单",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "deviation": 20,
    }
    result = mt5.order_send(request)
    order_id = result.order
    order_price = result.price
    return result, order_id, order_price


# 市价平空单
def stop_short_order(symbol, order_id, lot_size=0.1):
    price = mt5.symbol_info_tick(symbol).ask
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "position": order_id,
        "comment": "平空单",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,  # 改为IOC更灵活
        "deviation": 20,  # 添加允许的滑点
    }
    result = mt5.order_send(request)
    order_price = result.price
    return result, order_price
