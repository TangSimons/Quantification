import MetaTrader5 as mt5


# 市价买入函数
def create_order(symbol, lot_size=1.0):
    price = mt5.symbol_info_tick(symbol).ask
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "comment": "MA Crossover Strategy",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,  # 改为IOC更灵活
        "deviation": 10,  # 添加允许的滑点
    }
    result = mt5.order_send(request)
    order_id = result.order
    order_price = result.price
    return result, order_id,order_price


# 市价卖出函数
def stop_order(symbol, order_id, lot_size=1.0):
    price = mt5.symbol_info_tick(symbol).bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": mt5.ORDER_TYPE_SELL,
        "price": price,
        "position": order_id,  # 使用传入的order_id
        "comment": "MA Crossover Strategy",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "deviation": 10,
    }
    result = mt5.order_send(request)
    order_price = result.price
    return result,order_price

