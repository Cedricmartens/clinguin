
element(window, window, root).

h(500).
w(500).

attribute(window, height, X) :- h(X).
attribute(window, width, X) :- w(X).
attribute(window, background_color, black).
attribute(window, resizable_x, 0).
attribute(window, child_layout, grid).

amount(5).
p(0..(R*R-1)) :- amount(R).

element(c(X), container, window) :- p(X).
attribute(c(X), grid_column, X\R) :- p(X), amount(R).
attribute(c(X), grid_row, X/R) :- p(X), amount(R).
attribute(c(X), background_color, gray) :- p(X), X\2 == 1.
attribute(c(X), background_color, black) :- p(X), X\2 == 0.
attribute(c(X), height, H/R) :- p(X), h(H), amount(R).
attribute(c(X), width, W/R) :- p(X), w(W), amount(R).
attribute(c(X), child_layout, grid) :- p(X).


amount2(3).
q(X,0..(R*R-1)) :- p(X), amount2(R).

element(c(X,Y), container, c(X)) :- q(X,Y).
attribute(c(X,Y), grid_column, Y\R) :- q(X,Y), amount2(R).
attribute(c(X,Y), grid_row, Y/R) :- q(X,Y), amount2(R).
attribute(c(X,Y), background_color, blue) :- q(X,Y), Y\2 == 1, X\2 == 0.
attribute(c(X,Y), background_color, red) :- q(X,Y), Y\2 == 0, X\2 == 0.
attribute(c(X,Y), background_color, gray) :- q(X,Y), Y\2 == 1, X\2 == 1.
attribute(c(X,Y), background_color, white) :- q(X,Y), Y\2 == 0, X\2 == 1.
attribute(c(X,Y), height, H/(R1 * R2)) :- q(X,Y), h(H), amount(R1), amount2(R2).
attribute(c(X,Y), width, W/(R1 * R2)) :- q(X,Y), w(W), amount(R1), amount2(R2).



