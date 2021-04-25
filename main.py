import web
import numpy

numpy.int = int
numpy.float = float


if __name__ == '__main__':
    web.app.run()
