import sys
import random
from crossword import *

class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # Loop over every variable
        for domain in self.domains:
            # Create a list of values to remove to not change set's size while looping
            remove = []
            # Loop over every value in variable's domain
            for value in self.domains[domain]:
                # If the length of the value is different than the variable's size, add it to the remove list
                if len(value) != domain.length:
                    remove.append(value)
            # Remove every value in the list
            for value in remove:
                self.domains[domain].remove(value)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False

        # If there is an overlap between x and y
        if self.crossword.overlaps[x, y] is not None:
            # Save the x and y indexes
            x_idx, y_idx = self.crossword.overlaps[x, y]
            # Save the domain values to be removed in a set to not alter the loop range
            remove = set()

            # Compare the values in x.domain with the values in y.domain
            for x_value in self.domains[x]:
                # Create a flag
                removable = True
                # Loop over variable y's domain
                for y_value in self.domains[y]:
                    # If the value can be used
                    if x_value[x_idx] == y_value[y_idx]:
                        # Dont remove
                        removable = False
                        break
                # If it's not arc consistant, add to the remove set
                if removable:
                    remove.add(x_value)   

            # Remove the values tagged to remove from the domain of variable x, and return True, meaning changes were made
            for value in remove:
                self.domains[x].remove(value)
                revised = True
            
        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # If no arc given
        if arcs is None:
            queue = self.crossword.overlaps.copy()
        # Inference arc
        else:
            queue = arcs

        # Loop while there are items in the queue
        while len(queue) > 0:
            # Save the item keys (variable objects), and remove it
            x, y = list(queue.keys())[0]
            queue.pop((x, y))

            # Check with revise(x, y) if any value has to be removed
            if self.revise(x, y):
                # No solution if the domain of x is empty
                if len(self.domains[x]) == 0:
                    return False
                # Add the arcs of x and its neighbors to the queue
                for neighbor in (self.crossword.neighbors(x) - {y}):
                    overlap = self.crossword.overlaps[x, neighbor]
                    queue[x, neighbor] = overlap
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        # Check that the keys in assignment are the same as the varibales in the crossword
        if assignment.keys() == self.crossword.variables:
            return True
        return False

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # Loop, compairing every variable and value in assignment
        for x in assignment:
            for y in assignment:

                # Skip when checking the same
                if x == y:
                    continue
                
                # Check that values are distinct
                if assignment[x] == assignment[y]:
                    return False
                
                # Check overlap conflict
                if self.crossword.overlaps[x, y] != None:
                    x_idx, y_idx = self.crossword.overlaps[x, y]
                    if assignment[x][x_idx] != assignment[y][y_idx]:
                        return False
            
            # Check if the length of the value is consistant with the length of the variable
            if len(assignment[x]) != x.length:
                return False

        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # Create a dict with the values associated to the total of values removed in neighbors when assigned
        sums = {value: 0 for value in self.domains[var]}

        # Assign a value to var from its domain
        for value in self.domains[var]:
            # Check it against every neighbor of var
            for neighbor in self.crossword.neighbors(var):
                # Skip already assigned variables
                if neighbor in assignment:
                    continue
                # Check different words consistency, if the same value is in both domains, add 1 to value's sum
                if value in self.domains[neighbor]:
                    sums[value] += 1
                # Check arc consistency
                var_idx, neighbor_idx = self.crossword.overlaps[var, neighbor]
                for neighbor_value in self.domains[neighbor]:
                    if value[var_idx] != neighbor_value[neighbor_idx]:
                        sums[value] += 1

        # Sort the values by the total of words it rules out
        return dict(sorted(sums.items(), key=lambda sums: sums[1]))
        
        

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # Create a dictionary with unassigned variables as keys, and it's amount of values left in the domain and 
        # the amount of neighbors as values
        domains = {}
        for variable in self.crossword.variables:
            if variable in assignment.keys():
                continue
            domains[variable] = [len(self.domains[variable]), len(self.crossword.neighbors(variable))] 

        # Sort by MRV from lowest to highest
        domains = dict(sorted(domains.items(), key=lambda domain: domain[1][0]))

        # Check if more than one have the same MRV value
        first_key = list(domains.keys())[0]
        repeats_mrv = 0
        for variable in domains.keys():
            if domains[variable][0] == domains[first_key][0]:
                repeats_mrv += 1
        # If no repeats, return the lowest MRV
        if repeats_mrv == 1:
            return first_key

        # If there are more than one with the same MRV value
        else:
            # From the ones that have the same MRV, sort them by degree
            new_domain = list(domains.items())[:repeats_mrv]
            # Sort by degree from highest to lowest
            domains = dict(sorted(new_domain, key=lambda domain: domain[1][1], reverse=True)) # Only sort again the ones repeated
            first_key = list(domains.keys())[0]
            repeats_degree = []
            # Check if there are more than one with the same Degree of the mrv repeated variables
            for variable in domains.keys():
                if domains[variable][1] == domains[first_key][1]:
                    repeats_degree.append(variable)
            # If there are more than one
            if len(repeats_degree) > 1:
                # Return a random choice
                var = random.choice(repeats_degree)
                # Couldn't figure out why the variable object kinda broke when chosen with random library
                # So, search the random vriable in self.crossword.variables and return it
                for variable in self.crossword.variables:
                    if variable == var:
                        return variable
            # Else, return the one with the highest degree
            return repeats_degree[0]
       
            

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        
        # If assignment complete, return assignment
        if self.assignment_complete(assignment):
            return assignment

        # Select a an Unassigned Variable
        var = self.select_unassigned_variable(assignment)

        # Loop over the ordered values
        for value in self.order_domain_values(var, assignment):
            # Start by assigning the first value
            assignment[var] = value
            # If the value keeps the consistency in the problem
            if self.consistent(assignment):

                # Try inferring, looping over the variables
                for variable in self.crossword.variables:
                    # If the variable is unassigned and the domain has only 1 value, check assigning it
                    if variable not in assignment and len(self.domains[variable]) == 1:
                        # Create a queue for ac3
                        queue = {}
                        for neighbor in self.crossword.neighbors(variable):
                            queue[variable, neighbor] = self.crossword.overlaps[variable, neighbor]
                        # Check if the value in ac3 keeps the consistency
                        if self.ac3(queue):
                            # Assign the value if it works
                            for value in self.domains[variable]:
                                assignment[variable] = value
                        # Delete the assignment if it doesn't work, and try with the next unassigned variable with 1 value in its domain
                        else:
                            del assignment[variable]

                # Call backtrack recursiveness    
                result = self.backtrack(assignment)
                # If assignment done, return the assignment
                if result:
                    return result
            # Delete the value assigned if none of the previous conditions work, and check the next value
            del assignment[var]
        # Return None if after looping over every value there's no solution
        return None



def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
