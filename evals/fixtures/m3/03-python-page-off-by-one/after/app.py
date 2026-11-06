def page(items, number, size):
    start = (number - 1) * size
    end = start + size
    return items[start:end]
