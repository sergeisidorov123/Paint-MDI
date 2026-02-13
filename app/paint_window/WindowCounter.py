class WindowCounter:
    """Класс для отслеживания количества открытых окон рисования """
    __count_of_window = 0
    
    def increase_count(self):
        self.__count_of_window += 1

    def get_count(self): 
        return self.__count_of_window
    
    def reduce_count(self): 
        self.__count_of_window -= 1