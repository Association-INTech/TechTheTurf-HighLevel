/**
 * Example program for basic use of pico as an I2C peripheral (previously known as I2C slave)
 * 
 * This example allows the pico to act as a 256byte RAM
 * 
 * Author: Graham Smith (graham@smithg.co.uk)
 */


// Usage:
//
// When writing data to the pico the first data byte updates the current address to be used when writing or reading from the RAM
// Subsequent data bytes contain data that is written to the ram at the current address and following locations (current address auto increments)
//
// When reading data from the pico the first data byte returned will be from the ram storage located at current address
// Subsequent bytes will be returned from the following ram locations (again current address auto increments)
//
// N.B. if the current address reaches 255, it will autoincrement to 0 after next read / write


#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/irq.h"
#include "stdio.h"
#include "math.h"

// define I2C addresses to be used for this peripheral
#define I2C0_PERIPHERAL_ADDR 0x30

// GPIO pins to use for I2C
#define GPIO_SDA0 12
#define GPIO_SCK0 13


// ram_addr is the current address to be used when writing / reading the RAM
// N.B. the address auto increments, as stored in 8 bit value it automatically rolls round when reaches 255
uint8_t ram_addr = 0;

// ram is the storage for the RAM data
uint8_t ram[256];


union WriteBuffer {
    uint8_t buffer[8];
    float f_values[2];
};


union ReadBuffer {
    uint8_t buffer[24];
    float f_values[6];
};

struct ProgramState {
    float rho_target, theta_target, theta_kp, theta_ki, theta_kd, rho_kp, rho_ki, rho_kd;
    uint8_t powered;

    void (*write_callback)(void);
    uint8_t w_cnt, r_cnt;
    union WriteBuffer w;
    union ReadBuffer r;
};

struct ProgramState STATE;


void do_nothing() {}
void power() {
    if (STATE.w_cnt == 8) {
        STATE.powered = !!STATE.w.buffer[7];
        printf("PAMI est %s\n", (STATE.powered) ? "allumé" : "éteint");
    }
}
void move() {
    if (STATE.w_cnt == 8) {
        STATE.rho_target = STATE.w.f_values[1];
        STATE.theta_target = STATE.w.f_values[0];
        printf("Nouvelles valeurs cibles de rho/theta:\nrho = %f\ntheta = %f\n", STATE.rho_target, STATE.theta_target);
    }
}

void setup_read_write(uint8_t reg) {
    switch (reg) {
    case 0:
        STATE.write_callback = power;
        break;
    case 1:
        STATE.write_callback = move;
        break;
    case 2:
        STATE.write_callback = do_nothing;
        STATE.r.f_values[0] = STATE.theta_kp;
        STATE.r.f_values[1] = STATE.theta_ki;
        STATE.r.f_values[2] = STATE.theta_kd;
        STATE.r.f_values[3] = STATE.rho_kp;
        STATE.r.f_values[4] = STATE.rho_ki;
        STATE.r.f_values[5] = STATE.rho_kd;
        printf("Envoyes prametres de PID rho/theta:\ntheta_kp = %f\ntheta_ki = %f\ntheta_kd = %f\nrho_kp = %f\nrho_ki = %f\nrho_kd = %f\n",
            STATE.theta_kp,
            STATE.theta_ki,
            STATE.theta_kd,
            STATE.rho_kp,
            STATE.rho_ki,
            STATE.rho_kd
        );
        break;
    case 3:
    case 4:
        STATE.write_callback = do_nothing;
        STATE.r.f_values[0] = STATE.theta_target;
        STATE.r.f_values[1] = STATE.rho_target;
        printf("Envoyees valeurs cibles de rho/theta:\nrho = %f\ntheta = %f\n", STATE.rho_target, STATE.theta_target);
    default:
        break;
    }
}

// Interrupt handler implements the RAM
void i2c0_irq_handler() {


    // Get interrupt status
    uint32_t status = i2c0->hw->intr_stat;

    // Check to see if we have received data from the I2C controller
    if (status & I2C_IC_INTR_STAT_R_RX_FULL_BITS) {

        // Read the data (this will clear the interrupt)
        uint32_t value = i2c0->hw->data_cmd;

        // Check if this is the 1st byte we have received
        if (value & I2C_IC_DATA_CMD_FIRST_DATA_BYTE_BITS) {

            // If so treat it as the address to use
            STATE.w_cnt = 0;
            STATE.r_cnt = 0;
            setup_read_write(value);
            /* ram_addr = (uint8_t)(value & I2C_IC_DATA_CMD_DAT_BITS);
            printf("Address set to %d\n", ram_addr); */

        } else {
            // If not 1st byte then store the data in the RAM
            // and increment the address to point to next byte
            /* ram[ram_addr] = (uint8_t)(value & I2C_IC_DATA_CMD_DAT_BITS);
            printf("Set %d to %d\n", ram_addr, ram[ram_addr]); */
            STATE.w.buffer[STATE.w_cnt++] = value;
            STATE.write_callback();
        }
    }

    // Check to see if the I2C controller is requesting data from the RAM
    if (status & I2C_IC_INTR_STAT_R_RD_REQ_BITS) {

        // Write the data from the current address in RAM
        i2c0->hw->data_cmd = (uint32_t)STATE.r.buffer[STATE.r_cnt++];
        // Clear the interrupt
        i2c0->hw->clr_rd_req;

        // Increment the address
        ram_addr++;
    }
}


// Main loop - initilises system and then loops while interrupts get on with processing the data
int main() {
    stdio_init_all();

    // Setup I2C0 as slave (peripheral)
    i2c_init(i2c0, 100 * 1000);
    i2c_set_slave_mode(i2c0, true, I2C0_PERIPHERAL_ADDR);

    // Setup GPIO pins to use and add pull up resistors
    gpio_set_function(GPIO_SDA0, GPIO_FUNC_I2C);
    gpio_set_function(GPIO_SCK0, GPIO_FUNC_I2C);
    gpio_pull_up(GPIO_SDA0);
    gpio_pull_up(GPIO_SCK0);

    // Enable the I2C interrupts we want to process
    i2c0->hw->intr_mask = (I2C_IC_INTR_MASK_M_RD_REQ_BITS | I2C_IC_INTR_MASK_M_RX_FULL_BITS);

    // Set up the interrupt handler to service I2C interrupts
    irq_set_exclusive_handler(I2C0_IRQ, i2c0_irq_handler);

    // Enable I2C interrupt
    irq_set_enabled(I2C0_IRQ, true);

    // Do nothing in main loop
    while (true) {
        tight_loop_contents();
    }
    return 0;
}