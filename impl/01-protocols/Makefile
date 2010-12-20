CXXFILES = $(wildcard *.cpp)
OFILES = $(CXXFILES:.cpp=.o)
DEPFILES = $(CXXFILES:.cpp=.d)

CXXFLAGS = -g -Wall -Wextra -std=c++98
LDFLAGS = -Wall -Wextra

PROG = gps

.PHONY: all
all: $(PROG)

$(PROG): $(OFILES)
	$(CXX) $(LDFLAGS) -o $@ $^

.PHONY: clean
clean:
	rm -f $(LIB) $(OFILES) $(CPPFILES:.cpp=.d)

%.d: %.cpp
	$(CXX) $(CXXFLAGS) -MM -MT $@ -MT $(@:.d=.o) -MF $@ $<

-include $(DEPFILES)
