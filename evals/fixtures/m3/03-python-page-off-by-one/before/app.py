def page(items, number, size):
    start = (number - 1) * size
    end = start + size - 1
    return items[start:end]
