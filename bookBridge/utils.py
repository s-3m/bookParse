

def to_write_price_dict(need_list: list, id, price, sale_price = None):
    result_dict = {}
    result_dict['Артикул'] = id
    result_dict['Цена'] = price
    result_dict['Действующая цена'] = price
    if sale_price:
        result_dict['Цена со скидкой'] = sale_price
        result_dict['Действующая цена'] = sale_price

    need_list.append(result_dict)