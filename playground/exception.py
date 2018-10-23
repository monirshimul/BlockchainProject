def test():
    raise Exception("test function exception")


try:
    test()
except Exception as ex:
    print(str(ex))