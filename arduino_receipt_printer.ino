#include <RingBuffer.h> // Seems to be from Arduino IoT Cloud template, keep it for now.
#include "WiFiS3.h"
#include "thingProperties.h"
#include "EscPosCommands.h" // KEEP THIS INCLUDE!
#include <cctype>

// Define ESC/POS commands within the global scope (as they were in EscPosCommands.cpp)
// It's better to keep them in a separate .cpp file (EscPosCommands.cpp) and compile it.
// If you MUST put them directly in the .ino, define them like this.
// But the ideal way is to have EscPosCommands.h and EscPosCommands.cpp separately.
namespace EscPos{
    std::string CUT = {'\x1d', '\x56', '\x41', '\x02'}; // Changed \x96 to \x02 for common partial cut
    std::string RESET = {'\x1b', '\x40'};
    std::string FONT_A = {'\x1b', '\x4d', '\x00'};
    std::string FONT_B = {'\x1b', '\x4d', '\x01'};
    std::string UNDERLINE_OFF = {'\x1b', '\x2d', '\x00'};
    std::string UNDERLINE_1_DOT = {'\x1b', '\x2d', '\x01'};
    std::string UNDERLINE_2_DOT = {'\x1b', '\x2d', '\x02'};
    std::string BOLD_ON = {'\x1b', '\x45', '\x01'};
    std::string BOLD_OFF = {'\x1b', '\x45', '\x00'};
    std::string BITMAP = {'\x1b', '\x2a'}; // Note: BITMAP usage is complex, needs m, nL, nH and image data
    std::string NO_LINE = {'\x1b', '\x33', (unsigned char) 0};
    std::string RESET_LINE = {'\x1b', '\x32'};

    std::string BARCODE_PREFIX = {'\x1d', '\x6b', '\x49'};
    std::string CODE128_START_A_SYMBOL = {'\x7b', '\x41'};
    std::string BARCODE_12345678_TEST = {
        '\x1d', '\x6b', '\x49', '\x0a', '\x7b', '\x41',
        '\x31', '\x32', '\x33', '\x34', '\x35', '\x36', '\x37', '\x38'
    };

    std::string BARCODE_UPPERCASE_UUID_TEST = {
        '\x1d', '\x6b', '\x49', '\x26', // GS k 0x49, length 0x26 (38)
        '\x7b', '\x41', // Code128 Start Code A
        // Uppercased UUID: 2268441F-55D4-4482-9BC2-3FC6754C30C5
        '\x32', '\x32', '\x36', '\x38', '\x34', '\x34', '\x31', '\x46', // 2268441F (0x46 is 'F')
        '\x2d', // - (0x2D)
        '\x35', '\x35', '\x44', '\x34', // 55D4 (0x44 is 'D')
        '\x2d', // -
        '\x34', '\x34', '\x38', '\x32', // 4482
        '\x2d', // -
        '\x39', '\x42', '\x43', '\x32', // 9BC2 (0x42 is 'B', 0x43 is 'C')
        '\x2d', // -
        '\x33', '\x46', '\x43', '\x36', '\x37', '\x35', '\x34', '\x43', '\x33', '\x30', '\x43', '\x35' // 3FC6754C30C5 (0x46 'F', 0x43 'C')
    };

    // Alignment commands
    std::string ALIGN_LEFT = {'\x1b', '\x61', '\x00'};
    std::string ALIGN_CENTER = {'\x1b', '\x61', '\x01'};
    std::string ALIGN_RIGHT = {'\x1b', '\x61', '\x02'};

    std::string generateNumericCode128Barcode(const String& numericData) {
        for (unsigned int i = 0; i < numericData.length(); ++i) { // Use unsigned int for length
            if (!std::isdigit(numericData.charAt(i))) {
                return ""; // Invalid input
            }
        }
        // Use std::string internally for building the command as it's better for byte sequences
        std::string command;
        command.reserve(BARCODE_PREFIX.length() + 1 + CODE128_START_A_SYMBOL.length() + numericData.length());

        command += BARCODE_PREFIX;
        command += static_cast<char>(numericData.length() + CODE128_START_A_SYMBOL.length()); // Calculate n_byte_value directly
        command += CODE128_START_A_SYMBOL;

        // Append char by char from Arduino String to std::string
        for (unsigned int i = 0; i < numericData.length(); ++i) {
            command += numericData.charAt(i);
        }
        return command;
    }
}

WiFiServer server(80);

String urlDecode(String input) {
    String decoded = "";
    char temp[] = "0x00";
    unsigned int len = input.length();
    unsigned int i = 0;
    
    while (i < len) {
        char decodedChar;
        char encodedChar = input.charAt(i++);
        
        if ((encodedChar == '%') && (i + 1 < len)) {
            temp[2] = input.charAt(i++);
            temp[3] = input.charAt(i++);
            decodedChar = strtol(temp, NULL, 16);
        } else if (encodedChar == '+') {
            decodedChar = ' ';
        } else {
            decodedChar = encodedChar;
        }
        
        decoded += decodedChar;
    }
    
    return decoded;
}

namespace WebUtils {
    String extractQueryParameter(const String& header, const String& requestPath, const String& paramName) {
        String foundValue = "";
        int getStartIndex = header.indexOf("GET " + requestPath + "?");
        if (getStartIndex >= 0) {
            int queryStartIndex = getStartIndex + String("GET ").length() + requestPath.length() + 1;
            String queryString = header.substring(queryStartIndex);
            int httpVersionIndex = queryString.indexOf(" HTTP/1.1");
            if (httpVersionIndex >= 0) {
                queryString = queryString.substring(0, httpVersionIndex);
            }
            String searchKey = paramName + "=";
            int paramStart = 0;
            int paramEnd = 0;
            while (paramEnd != -1) {
                paramEnd = queryString.indexOf('&', paramStart);
                String param;
                if (paramEnd == -1) {
                    param = queryString.substring(paramStart);
                } else {
                    param = queryString.substring(paramStart, paramEnd);
                }
                if (param.startsWith(searchKey)) {
                    foundValue = param.substring(searchKey.length());
                    // If urlDecode is needed for /print, you'd call it here for textToPrint
                    // For barcodeData, we explicitly decided against it.
                    break;
                }
                paramStart = paramEnd + 1;
            }
        }
        return foundValue;
    }
}

void setup() {
  Serial.begin(115200); // Use 115200 for debug monitor
  Serial1.begin(9600); // Set to your printer's baud rate for Serial1
  
  // This delay gives the chance to wait for a Serial Monitor without blocking if none is found
  delay(1500); 

  initProperties(); // From thingProperties.h
  ArduinoCloud.begin(ArduinoIoTPreferredConnection);
  setDebugMessageLevel(2); // Higher debug level for IoT Cloud connection info
  ArduinoCloud.printDebugInfo();

  server.begin(); // Start the HTTP server

  Serial.println("Arduino HTTP Server Ready!");
  Serial.print("Access your board at http://");
  Serial.println(WiFi.localIP()); // Print IP to Serial Monitor
  Serial.print("Printer Serial (Serial1) initialized at ");
  Serial.print(9600); // Or whatever PRINTER_BAUD_RATE you're using for Serial1
  Serial.println(" baud.");
}

void loop() {
  ArduinoCloud.update(); // Keep IoT Cloud connection alive
  
  WiFiClient client = server.available(); // Check for new clients
  if (client) {
    Serial.println("\nNew Client Connected."); // Debug: New connection
    String currentLine = "";
    String header = "";
    String printText = ""; // Declare here to be accessible after parsing loop

    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        header += c;
        // Serial.write(c); // Uncomment this if you want to see raw incoming HTTP request

        if (c == '\n') {
          if (currentLine.length() == 0) { // End of HTTP header
            
            if (header.indexOf("GET /print") >= 0) {
              Serial.println("Processing /print request.");
              
              int queryStartIndex = header.indexOf("GET /print?") + 11;
              
              if (queryStartIndex >= 11) {
                  String queryString = header.substring(queryStartIndex);
                  int httpVersionIndex = queryString.indexOf(" HTTP/1.1");
                  if (httpVersionIndex >= 0) {
                      queryString = queryString.substring(0, httpVersionIndex);
                  }

                  Serial.print("Raw Query String: "); Serial.println(queryString);

                  int paramStart = 0;
                  int paramEnd = 0;
                  while (paramEnd != -1) {
                      paramEnd = queryString.indexOf('&', paramStart);
                      String param;
                      if (paramEnd == -1) {
                          param = queryString.substring(paramStart);
                      } else {
                          param = queryString.substring(paramStart, paramEnd);
                      }

                      Serial.print("  Parsing param: "); Serial.println(param);

                      if (param.startsWith("text=")) {
                          printText = param.substring(5);
                          printText = urlDecode(printText);  // This handles ALL URL encoding
                          Serial.print("    Found Text: ");
                          Serial.println(printText);
                      }
                      
                      paramStart = paramEnd + 1;
                  }

              } else {
                  Serial.println("No query string found after /print.");
              }
              
              // --- NOW, SEND THE PARSED CONTENT TO THE PRINTER ---
              Serial.println("\n--- Sending to Physical Printer (Serial1) ---");
              
              // Optional: Initialize printer before each print job
              Serial1.write(EscPos::RESET.c_str(), EscPos::RESET.length()); 
              delay(100); // Give printer a moment after reset

              // You can apply formatting here, e.g.:
              // Serial1.write(EscPos::BOLD_ON.c_str(), EscPos::BOLD_ON.length());
              // Serial1.write(EscPos::FONT_B.c_str(), EscPos::FONT_B.length());
              
              Serial1.print(printText); // Send the actual decoded text to printer

              // Optional: Add a small delay for the printer to finish before closing connection
              delay(500); 

              // Send HTTP response back to the browser
              client.println("HTTP/1.1 200 OK");
              client.println("Content-Type: text/plain");
              client.println("Connection: close");
              client.println();
              client.println("Print request sent to printer!");
              client.print("Text: "); client.println(printText.length() > 0 ? printText : "[None]");
              
            } else if (header.indexOf("GET / ") >= 0 || header.indexOf("GET /index.html") >= 0) {
              Serial.println("Processing / (root) request.");
              client.println("HTTP/1.1 200 OK");
              client.println("Content-Type: text/html");
              client.println("Connection: close");
              client.println();
              client.println("<!DOCTYPE HTML>");
              client.println("<html><body><h1>Arduino Printer Server v0.0.8</h1>");
              client.println("<p>Send text to: <code>http://YOUR_ARDUINO_IP/print?text=Hello%20World%26priority=1</code></p>");
              client.println("<p>Visit <a href=\"/print?text=Test&priority=0\">/print</a> for a quick test.</p>");
              client.println("</body></html>");
              
            } else if (header.indexOf("GET /cut ") >= 0) {
              Serial.println("Processing / (root) request.");
              client.println("HTTP/1.1 200 OK");
              client.println("Content-Type: text/html");
              client.println("Connection: close");
              client.println();
              client.println("<!DOCTYPE HTML>");
              client.println("<html><body><h1>Arduino Printer Server</h1>");
              client.println("<p>CUT Processed</p>");
              client.println("</body></html>");
              // --- CUT COMMAND HERE! ---
              // This command should come AFTER all the text has been sent.
              Serial.print("Sending CUT command to printer (Serial1).");
              Serial1.write(EscPos::CUT.c_str(), EscPos::CUT.length());
              Serial.println(" Cut command sent.");
              
            } else if (header.indexOf("GET /barcode?") >= 0) {
              client.println("HTTP/1.1 200 OK");
              client.println("Content-Type: text/html");
              client.println("Connection: close");
              client.println();
              client.println("<!DOCTYPE HTML>");
              client.println("<html><body><h1>Arduino Printer Server</h1>");
              client.println("<p>BARCODE Processed</p>");
              
              Serial.println("/barcode test."); // Short debug print
              String barcodeData = WebUtils::extractQueryParameter(header, "/barcode", "barcode");

              if (!barcodeData.isEmpty()) {
                  client.print("<p>Test for: "); client.print(barcodeData); client.println("</p>");
                  Serial.print("Test for: "); Serial.println(barcodeData);

                  std::string generatedCommand = EscPos::generateNumericCode128Barcode(barcodeData);

                  // Compare only if the input is "12345678"
                  if (!generatedCommand.empty()) {
                      Serial1.write(EscPos::ALIGN_CENTER.c_str(), EscPos::ALIGN_CENTER.length());
                      delay(10);
                      Serial1.write(generatedCommand.c_str(), generatedCommand.length());
                      delay(10);
                      Serial1.write("\n");
                      delay(10);
                      Serial1.write(EscPos::ALIGN_LEFT.c_str(), EscPos::ALIGN_LEFT.length());
                      delay(10);
                      Serial1.write(EscPos::RESET.c_str(), EscPos::RESET.length());
                      delay(50);
                      client.println("<p>Barcode command sent to printer.</p>");
                  } else {
                      // For other numeric inputs, just confirm it was generated
                      client.println("<p>Generated command for input (not 12345678).</p>");
                      Serial.println("Generated for other input.");
                  }
              } else {
                  client.println("<p>Error: No barcode data or non-numeric.</p>");
                  Serial.println("Error: No data/non-numeric.");
              }
              client.println("</body></html>");
            } else if (header.indexOf("GET /barcode/uuid_static_test") >= 0) {
                Serial.println("Processing /barcode/uuid_static_test (STATIC UUID PRINT ATTEMPT).");
                client.println("HTTP/1.1 200 OK");
                client.println("Content-Type: text/html");
                client.println("Connection: close");
                client.println();
                client.println("<!DOCTYPE HTML><html><body><h1>Arduino Printer Server</h1>");
                client.println("<p>Attempting to print STATIC UPPERCASE UUID Barcode.</p>");

                // --- CRITICAL: Send the static string directly to the printer ---
                Serial1.write(EscPos::BARCODE_UPPERCASE_UUID_TEST.c_str(), EscPos::BARCODE_UPPERCASE_UUID_TEST.length());
                delay(10);
                Serial1.write("\n"); // Newline is CRITICAL
                delay(10);
                Serial1.write(EscPos::RESET.c_str(), EscPos::RESET.length()); // RESET is CRITICAL
                delay(50);

                client.println("<p>Uppercase UUID Barcode command sent to printer. It failed. Leaving this here for later maybe.</p>");
                Serial.println("Uppercase UUID Barcode command sent.");

                client.println("</body></html>");
            } else {
              Serial.println("Request for unknown path (404).");
              client.println("HTTP/1.1 404 Not Found");
              client.println("Content-Type: text/plain");
              client.println("Connection: close");
              client.println();
              client.println("404 Not Found. Try / or /print");
            }
            
            break; // Exit the while (client.connected()) loop after handling request
          } else {    // If it's not a blank line, it's part of the header
            currentLine = ""; // Clear currentLine for the next header line
          }
        } else if (c != '\r') {  // If not a carriage return
          currentLine += c;      // Add it to the end of the currentLine
        }
      } else { // No data currently available from client
        delay(1); // Yield control for a moment
        // If client disconnected abruptly before sending any data, exit
        if (!client.connected() && header.length() == 0) {
            Serial.println("Client disconnected prematurely."); // Debug
            break;
        }
      } 
    }

    Serial.println("Client session ended."); // Debug
    delay(3); // Small delay to ensure browser received response
    client.stop(); // Close the connection
  }
}
