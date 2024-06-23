#include <hello_world/hello_world.h>

#include <sstream>

int main()
{
    std::stringstream ss;
    say_hello_world(ss);

    if (ss.str() != "Hello world!\n") {
        std::cout << "Failed\n";
    } else {
        std::cout << "Succeeded\n";
    }

    return 0;
}