import PySimpleGUI as sg
import itertools
import random
import copy
# Debugging Imports
from pprint import pprint
from time import sleep
# https://docs.pysimplegui.com/en/latest/

def run_example():
    # All the stuff inside your window.
    layout = [  [sg.Text("What's your name?")],
                [sg.InputText()],
                [sg.Button('Ok'), sg.Button('Cancel')] ]

    # Create the Window
    window = sg.Window('Hello Example', layout)

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()

        # if user closes window or clicks cancel
        if event == sg.WIN_CLOSED or event == 'Cancel':
            break

        print('Hello', values[0], '!')

    window.close()


class SchellingSimulation:
    X_Agents = 23
    O_Agents = 23
    MAX_ROWS = MAX_COL = 8
    NeigborPreference = 4
    SIMULATION_ITERATION_LIMIT = 100

    _ListOfSimulationArrays: list = []
    _SimulationIterationNumber = 0

    def __init__(self,*, X_Agents: int = 23, O_Agents: int = 23, NeigborPreference: int = 2) -> None:
        if self.X_Agents + self.O_Agents > self.MAX_ROWS * self.MAX_COL:
            raise Exception('Too many agents to place in the grid')
        
        if self.X_Agents < 0 or self.O_Agents < 0:
            raise Exception('Cannot have negative agents')

        if self.NeigborPreference < 0:
            raise Exception('Cannot have negative NeigborPreference')

        if self.NeigborPreference > 8:
            raise Exception('NeigborPreference cannot be greater than 8. This is a geometrical limitation.')
        
        self.X_Agents = X_Agents
        self.O_Agents = O_Agents
        self.NeigborPreference = NeigborPreference
    
    def run(self):

        layout = [[sg.Button(str('Previous'), size=(7,2)), sg.Button(str('Next'), size=(7,2)), sg.Text(str(''), key="Current Iteration", size=(15,2))]]

        layout += [[sg.Button(str(' '), size=(4, 2), pad=(0,0), border_width=1, key=(row,col)) for col in range(self.MAX_COL)] for row in range(self.MAX_ROWS)]

        layout += [[sg.Button(str('Run Simulation'), size=(7,2)), sg.Text(str(''), text_color='red', size=(25,3), key='PostSim Iteration Count')]]

        window = sg.Window('Hello Example', layout)

        currentlyViewedIteration = 0

        while True:
            event, values = window.read()

            print(event)

            match event:
                case 'Run Simulation':
                    self._ListOfSimulationArrays = []
                    self._SimulationIterationNumber = currentlyViewedIteration = 0
                    self.execute_simulation()
                    window["PostSim Iteration Count"].update(str(f'Total Number of Iterations: {self._SimulationIterationNumber}'))
                    self.loadSimulationGridToWindow(window, currentlyViewedIteration)
                    window["Current Iteration"].update(str(f'Viewing Iteration: {currentlyViewedIteration}'))

                case 'Next':
                    if currentlyViewedIteration + 1 > self._SimulationIterationNumber: currentlyViewedIteration = 0
                    else: currentlyViewedIteration += 1

                    self.loadSimulationGridToWindow(window, currentlyViewedIteration)
                    window["Current Iteration"].update(str(f'Viewing Iteration: {currentlyViewedIteration}'))
                case 'Previous':
                    if currentlyViewedIteration - 1 < 0: currentlyViewedIteration = self._SimulationIterationNumber
                    else: currentlyViewedIteration -= 1

                    self.loadSimulationGridToWindow(window, currentlyViewedIteration)
                    window["Current Iteration"].update(str(f'Viewing Iteration: {currentlyViewedIteration}'))
                case _:
                    print('Unhandled event: ', event)

            if event == sg.WIN_CLOSED: break

        window.close()

    def loadSimulationGridToWindow(self, window: sg.Window, iterationNumber: int) -> None:

        for (row,col) in [pair for pair in itertools.product(range(self.MAX_ROWS), range(self.MAX_COL))]:
            window[(row,col)].update(self._ListOfSimulationArrays[iterationNumber][row][col])

        window["Current Iteration"].update(str(f'Viewing Iteration: {iterationNumber}'))


    def execute_simulation(self) -> None:

        simulationGrid = [[' ' for col in range(self.MAX_COL)] for row in range(self.MAX_ROWS)]
        # First, we must randomly distribute the agents in the 64 grid space.
        # To do so, we produce a list of all possible coordinates, where each element is a unique two-tuple vector in our space.
        coordinatePairs = [pair for pair in itertools.product(range(self.MAX_ROWS), range(self.MAX_COL))]
        
        # With a list of every coordinate pair, we can now randomly distribute the agents. First, we a select
        # a random index in the list, and that will be its location for the simulation. Then, we remove that
        # index from the list of coordinates.

        # We also construct an array of 'X's and 'O's to represent the agents.
        # We remove enteries in this array for the agents that have already been placed.

        agentList = ['X' for _ in range(self.X_Agents)] + ['O' for _ in range(self.O_Agents)]

        random.shuffle(coordinatePairs)
        random.shuffle(agentList)

        for (agent, (row,col)) in zip(agentList, coordinatePairs):
            simulationGrid[row][col] = agent
        
        self._ListOfSimulationArrays.append(copy.deepcopy(simulationGrid))
        
        
        # Now that we've generated the inital grid, we can move forward with the simulation.

        while True:
            # First, check each agent to see if they're satisfied with their position.
            # If they are, then we can move on to the next agent.
            # If they are not, we list them in the 'angry resident' list by coordinate and type.
            angryResidents = []

            # We create a list of empty spaces so angry agents know where to move.
            emptySpaces = []

            for (row,col) in [pair for pair in itertools.product(range(self.MAX_ROWS), range(self.MAX_COL))]:
                agentType = simulationGrid[row][col]
                if agentType == ' ':
                    emptySpaces.append(
                        {'location': (row,col), 'neighbors': self.getNeighboorTypes(row,col,simulationGrid)}
                    )
                else:
                    if self.getNeighboorTypes(row,col,simulationGrid).count(agentType) <= self.NeigborPreference:
                        angryResidents.append((row,col,agentType))
        

            if len(angryResidents) <= 0: break # This point should only be reached if no angry residents are found, meaning the simulation has reached steady state
            
            random.shuffle(angryResidents)

            for (row,col,agentType) in angryResidents:
                emptySpaces.sort(key=lambda spaceData: spaceData['neighbors'].count(agentType), reverse=True)
                ideal_space_row, ideal_space_col = emptySpaces[0]['location']
                
                emptySpaces.pop(0) # Space is now taken.

                # We switch the agents and the empty space.
                simulationGrid[ideal_space_row][ideal_space_col] = agentType
                simulationGrid[row][col] = ' '

                if len(emptySpaces) <= 0: break # Ran out of spaces
            
            self._ListOfSimulationArrays.append(copy.deepcopy(simulationGrid))
            self._SimulationIterationNumber += 1

            if self._SimulationIterationNumber >= self.SIMULATION_ITERATION_LIMIT: break # We've reached steady state

    def getNeighborCoordinates(self, row, col) -> list[tuple[int,int]]:
        neighborhood_range_row = range(row - 1 if row > 0 else row, 
                                        (row + 1 if row < self.MAX_ROWS - 1 else row) + 1
                                        )
        neighborhood_range_col = range(col - 1 if col > 0 else col, 
                                        (col + 1 if col < self.MAX_COL - 1 else col) + 1
                                        )

        return [(i,j) for (i,j) in itertools.product(neighborhood_range_row, neighborhood_range_col) if ((i,j) != (row,col))]
        
    def getNeighboorTypes(self, x,y, simulationGrid) -> list[str]:
        return [simulationGrid[i][j] for (i,j) in self.getNeighborCoordinates(x,y)]

SchellingSimulation().run()